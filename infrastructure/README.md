# Infrastructure

Everything that runs Docetra outside application code: the Docker stack, environment files, the production reverse proxy, and operations scripts.

```text
infrastructure/
├── docker-compose.yml          # nginx (static SPA + API edge) + api (+APScheduler) + worker + postgres + redis + rabbitmq + minio
├── .env                        # REAL local values (gitignored — never commit)
├── .env.example                # template with CHANGE_ME placeholders + production checklist
├── nginx/
│   ├── docker.conf             # containerized edge (static SPA + /api proxy) used by Compose
│   └── docetra.conf.example    # host reverse proxy template (HTTPS, /api → :8000, / → :8080)
└── scripts/                    # up / down / logs / backup (PowerShell + bash)
```

## Environment files — one source of truth

`.env` next to `docker-compose.yml` drives **both** container env and Compose `${...}` interpolation. Compose auto-loads it from this directory, so no `--env-file` flag is needed for local use.

```bash
# from anywhere (paths relative to repo root)
docker compose -f infrastructure/docker-compose.yml up -d

# or from this folder
cd infrastructure && docker compose up -d
```

For production:

```bash
cp .env.example .env.production   # fill in every CHANGE_ME, follow the checklist inside
docker compose --env-file .env.production -f docker-compose.yml up -d
```

Generate secrets: `python -c "import secrets; print(secrets.token_hex(32))"`
Rotate immediately if a real `.env` is ever shared or committed.

## Services (small team, ~20 users)

| Service | Purpose | Loopback port |
| --- | --- | --- |
| nginx | Sole edge + static SPA host: serves the Nuxt SPA, proxies `/api/` → FastAPI | `HTTP_PORT` (8080) |
| api | FastAPI HTTP (`/api/v2`) + APScheduler (`SCHEDULER_IN_API=true`) | 8000 |
| worker | RabbitMQ consumers: Drive sync, exports, notifications | — |
| telegram | Dedicated Telegram bot (long polling): menus, reminders, reset codes | — |
| postgres | Business + authorization truth | 5432 |
| redis | Session/operational state (DB 0) + cache tiers (DB 1/2) | 6379 |
| rabbitmq | Job queue between api → worker | 15672 (UI) |
| minio | S3-compatible object storage for attachments/exports | 9000 / 9001 (UI) |

The frontend is a **static SPA served by nginx** (no Node runtime container). For this small stack APScheduler runs inside the API (`SCHEDULER_IN_API=true`); set it to `false` and run `python -m app.main scheduler` separately when scaling to multiple API workers/instances. The worker stays a separate process, and the Telegram bot runs in its own `telegram` container so chat traffic never competes with job consumption. Local ports can be changed per machine in `.env` (e.g. `BACKEND_PORT=8001`). Browse the app at `http://localhost:${HTTP_PORT}` (default 8080); the browser talks to nginx and `/api/v2` is proxied to FastAPI on the same origin.

## Operations scripts

| Task | Windows | Linux / VPS |
| --- | --- | --- |
| Start | `.\infrastructure\scripts\up.ps1` | `./infrastructure/scripts/up.sh` |
| Start + rebuild images | `.\infrastructure\scripts\up.ps1 -Build` | `./infrastructure/scripts/up.sh --build` |
| Stop | `.\infrastructure\scripts\down.ps1` | `./infrastructure/scripts/down.sh` |
| Stop + wipe data | `.\infrastructure\scripts\down.ps1 -Volumes` | `./infrastructure/scripts/down.sh -v` |
| Follow logs | `.\infrastructure\scripts\logs.ps1` | `./infrastructure/scripts/logs.sh` |
| Backup DB + files | `.\infrastructure\scripts\backup.ps1` | `./infrastructure/scripts/backup.sh` |

## Production deployment (single box)

1. Install Docker (nginx is part of the stack); clone the repo.
2. `cp infrastructure/.env.example infrastructure/.env.production` and fill in every value (checklist at the bottom of the template — the backend refuses to boot in production until it passes validation). Set `HTTP_PORT` and `NUXT_PUBLIC_SITE_URL` to your public origin.
3. `cd infrastructure && docker compose --env-file .env.production up -d --build`
4. The app is served by the `nginx` container on `HTTP_PORT`. For TLS on a real domain, run the host reverse proxy from `nginx/docetra.conf.example` (certbot) in front and point it at `127.0.0.1:${HTTP_PORT}`, or add certs to `nginx/docker.conf`.
5. Schedule `scripts/backup.sh` daily via cron (Task Scheduler on Windows).

## CI

GitHub Actions (`.github/workflows/ci.yml`) uses this same compose file with CI-generated secrets and waits on `http://127.0.0.1:8000/ready` before integration/E2E tests. After the full suite passes on a `dev`/`main` push, the `deploy` job SSHes to the production box and runs this compose file with `infrastructure/.env.production` — see `docs/DEPLOYMENT.md` for the required secrets.
