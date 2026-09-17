# Infrastructure

Everything that runs Docetra outside application code: the Docker stack, environment files, the production reverse proxy, and operations scripts.

```text
infrastructure/
├── docker-compose.yml          # api + worker + scheduler + postgres + redis + rabbitmq + minio
├── .env                        # REAL local values (gitignored — never commit)
├── .env.example                # template with CHANGE_ME placeholders + production checklist
├── nginx/
│   └── docetra.conf.example    # reverse proxy template (HTTPS, /api → :8000, / → :3000)
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
| api | FastAPI HTTP (`/api/v2`) | 8000 |
| worker | RabbitMQ consumers: Drive sync, exports, notifications | — |
| scheduler | APScheduler: meeting reminders, reconciliation, cleanup | — |
| postgres | Business + authorization truth | 5432 |
| redis | Session/operational state (DB 0) + cache tiers (DB 1/2) | 6379 |
| rabbitmq | Job queue between api → worker | 15672 (UI) |
| minio | S3-compatible object storage for attachments/exports | 9000 / 9001 (UI) |

Worker and scheduler always stay separate processes — never fold jobs into the API. Local ports can be changed per machine in `.env` (e.g. `BACKEND_PORT=8001`).

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

1. Install Docker + nginx; clone the repo.
2. `cp infrastructure/.env.example infrastructure/.env.production` and fill in every value (checklist at the bottom of the template — the backend refuses to boot in production until it passes validation).
3. `cd infrastructure && docker compose --env-file .env.production up -d --build`
4. Run the Nuxt frontend on the host (`127.0.0.1:3000`, node-server preset + systemd/pm2).
5. Copy `nginx/docetra.conf.example` to `/etc/nginx/sites-available/docetra.conf`, set the real domain, run `certbot --nginx`, reload nginx.
6. Schedule `scripts/backup.sh` daily via cron (Task Scheduler on Windows).

## CI

GitHub Actions (`.github/workflows/ci.yml`) uses this same compose file with CI-generated secrets and waits on `http://127.0.0.1:8000/ready` before integration/E2E tests.
