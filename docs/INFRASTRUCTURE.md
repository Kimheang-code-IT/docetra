# Docetra — Infrastructure

Verified implementation: `infrastructure/docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `infrastructure/nginx/docker.conf`, `infrastructure/nginx/docetra.conf.example`, `infrastructure/scripts/*`, `.github/workflows/ci.yml`.

## Topology (single-box, ~20 users target)

```
            ┌────────────── edge network ──────────────┐
nginx :8080 ─┬─► static SPA (/usr/share/nginx/html, baked into the image)
             └─► api (FastAPI/uvicorn :8000 + APScheduler, loopback publish)
            postgres :5432 (loopback)   redis :6379 (loopback)
            rabbitmq :5672 (mgmt :15672 loopback)       minio :9000/:9001 (loopback)
            └────────────── private network ──────────┐
            worker (python -m app.main worker)  ── private
            telegram (python -m app.main telegram) ── edge (outbound only)
```

The frontend is a static SPA; there is no Node runtime container. For this small stack APScheduler runs inside the API process (`SCHEDULER_IN_API=true`); disable it and run `python -m app.main scheduler` as a separate process when scaling to multiple API workers/instances.

Services (compose):

| Service | Image | Notes |
|---|---|---|
| nginx | built `frontend/Dockerfile` (node build → nginx:1.27-alpine) | sole edge: serves the static SPA and proxies `/api/`, `/health`, `/ready` to api; host `HTTP_PORT` (8080); config `nginx/docker.conf` |
| api | built `backend/Dockerfile` (python 3.12-slim, pinned digest) | runs `alembic upgrade head` then uvicorn; healthcheck `/health`; **read-only fs, cap_drop ALL, no-new-privileges, tmpfs /tmp**; APScheduler via `SCHEDULER_IN_API=true` |
| worker | same image | RabbitMQ consumers (exports, outbox); private network only |
| telegram | same image | dedicated Telegram bot long-polling process (`python -m app.main telegram`); edge network for outbound API calls |
| postgres | pinned digest | volume `postgres_data`; loopback port for DB tools |
| redis | pinned digest | AOF + snapshot; ops DB 0, cache DB 1 |
| rabbitmq | 3.13-management | vhost `docetra`; mgmt UI loopback |
| minio | `quay.io/minio/minio` (`MINIO_IMAGE` override) | S3 API + console; volume `minio_data` |
| postgres-backup / minio-backup | `--profile operations` | one-shot pg_dump / mc mirror into `backend_backups` volume |

Networks: `edge` (published) + `private` (internal-only: backups). The worker is on **both** `edge` and `private` because it needs outbound internet for SMTP/Telegram/Google Drive. Env comes from a single `.env` next to the compose file (`BACKEND_ENV_FILE` override; production: `--env-file .env.production`).

## Backend image

- Non-root user `docetra` (uid 10001), no bytecode, pinned base digest.
- CMD: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers`.

## Nginx

Two configs:

- `infrastructure/nginx/docker.conf` — containerized edge used by Compose (HTTP only). Serves the static SPA from `/usr/share/nginx/html` with history-mode fallback (`$uri/index.html` → `$uri` → `/200.html`), immutable caching for `/_nuxt/`, and the production security headers/CSP (mirrors `frontend/nuxt.config.ts`). `/api/`, `/health`, `/ready` proxy to `api:8000` using Docker DNS re-resolution. Upload limit 26 MB; `/healthz` for the container healthcheck.
- `infrastructure/nginx/docetra.conf.example` — host nginx template for a real domain (TLS via certbot). Point it at the published nginx container port (`127.0.0.1:${HTTP_PORT}`).

The SPA is built with `NUXT_STATIC_SPA=true` (`pnpm generate`, Nitro `static` preset) and served **only through nginx**; the browser uses same-origin `/api/v2`, which nginx proxies to FastAPI.

## Operations scripts

`infrastructure/scripts/`: `up.sh/.ps1`, `down.sh/.ps1`, `logs.sh/.ps1`, `backup.sh/.ps1` — wrap compose commands (backup runs the operations-profile services).

## CI (`.github/workflows/ci.yml`)

1. **Secret scan**: gitleaks.
2. **Backend**: ruff lint, compileall, `pytest` with coverage (fail-under 35), coverage artifact.
3. **Frontend**: pnpm install, lint (eslint), typecheck (nuxt typecheck), unit tests, (build in extended job).
4. Concurrency-canceled per ref; pinned action SHAs; read-only token scope.

## Environment variables (selection; full list in `core/config.py`)

`DATABASE_URL`, `REDIS_URL`, `CACHE_SHORT_URL`, `RABBITMQ_URL`, `S3_ENDPOINT/KEY/SECRET/BUCKET`, `SESSION_SECRET`, `JWT_SECRET`, `PASSWORD_RESET_SECRET`, `SETTINGS_ENCRYPTION_KEY`, `SESSION_COOKIE_SECURE`, SMTP_*, TELEGRAM_*, GOOGLE_DRIVE_*, `MAX_UPLOAD_SIZE_MB`, `WORKER_CONCURRENCY`, `SCHEDULER_*`, `BACKEND_PORT`, `POSTGRES_*`, `RABBITMQ_*`, `MINIO_*`, `DOCETRA_COMPOSE_PROJECT`.

## Sizing/limits

- RabbitMQ single-node broker OK for ~20 users (`docetra.events` exchange + `docetra.dlx` dead-letter).
- Scheduler: APScheduler, UTC, misfire grace 300s, coalesce on.
- Worker: concurrency 2, prefetch 2 (defaults).
