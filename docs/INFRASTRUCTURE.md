# Docetra — Infrastructure

Verified implementation: `infrastructure/docker-compose.yml`, `backend/Dockerfile`, `infrastructure/nginx/docetra.conf.example`, `infrastructure/scripts/*`, `.github/workflows/ci.yml`.

## Topology (single-box, ~20 users target)

```
            ┌────────────── edge network ──────────────┐
nginx ──►   api (FastAPI/uvicorn :8000, loopback publish)
            postgres :5432 (loopback)   redis :6379 (loopback)
            rabbitmq :5672 (mgmt :15672 loopback)       minio :9000/:9001 (loopback)
            └────────────── private network ──────────┐
            worker (python -m app.main worker)  ── private
            scheduler (python -m app.main scheduler) ── private
            redis-ui :8081 (dev only)
```

Services (compose):

| Service | Image | Notes |
|---|---|---|
| api | built `backend/Dockerfile` (python 3.12-slim, pinned digest) | runs `alembic upgrade head` then uvicorn; healthcheck `/health`; **read-only fs, cap_drop ALL, no-new-privileges, tmpfs /tmp** |
| worker | same image | RabbitMQ consumers (exports, outbox); private network only |
| scheduler | same image | APScheduler: cleanup, meeting reminders, reconcile |
| postgres | pinned digest | volume `postgres_data`; loopback port for DB tools |
| redis | pinned digest | AOF + snapshot; ops DB 0, cache DB 1 |
| rabbitmq | 3.13-management | vhost `docetra`; mgmt UI loopback |
| minio | pinned digest | S3 API + console; volume `minio_data` |
| redis-ui | dev only | loopback :8081 |
| postgres-backup / minio-backup | `--profile operations` | one-shot pg_dump / mc mirror into `backend_backups` volume |

Networks: `edge` (published) + `private` (internal: worker, scheduler, backups). Env comes from a single `.env` next to the compose file (`BACKEND_ENV_FILE` override; production: `--env-file .env.production`).

## Backend image

- Non-root user `docetra` (uid 10001), no bytecode, pinned base digest.
- CMD: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers`.

## Nginx

`infrastructure/nginx/docetra.conf.example` — TLS termination + reverse proxy to api; frontend served separately (static build). **Needs verification**: no frontend Dockerfile — frontend deploys as static Nuxt build (`pnpm build`) behind nginx or its own server.

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
