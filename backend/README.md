# Docetra backend

FastAPI API, RabbitMQ worker, and APScheduler process. Matches the Nuxt adapters in `frontend/app/utils/constants/api-endpoints.ts`.

## Processes

| Command | Role |
| --- | --- |
| `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000` | HTTP API |
| `python -m app.worker` | Outbox publisher, export completion, queue consumers |
| `python -m app.scheduler` | UTC meeting reminder / reconcile ticks |

## Local Docker

From the repository root:

```powershell
Copy-Item backend.env.example backend.env
docker compose --env-file backend.env -f compose.backend.yml up --build -d
```

Default admin (development): `admin@gmail.com` / `123456`. Production startup fails closed when secrets, HTTPS cookies, CORS, trusted hosts, or the admin password are unsafe. Use `backend.env.production.example` as the deployment checklist.

Generate independent secrets without installing tooling on the host:

```powershell
docker run --rm python:3.12-slim python -c "import secrets; [print(secrets.token_urlsafe(48)) for _ in range(6)]"
```

Then start with `BACKEND_ENV_FILE=backend.env.production` (already present in the production template):

```powershell
docker compose --env-file backend.env.production -f compose.backend.yml up --build -d
```

Local and production templates use different `DOCETRA_COMPOSE_PROJECT` values. Keep them different: PostgreSQL, RabbitMQ, Redis, MinIO, and backup volumes must never be shared between environments. If an environment file is changed, recreate containers with that same file instead of using `docker compose restart`.

Point Nuxt at the API:

```env
NUXT_PUBLIC_USE_MOCK_DATA=false
NUXT_PUBLIC_API_BASE=http://localhost:8000
NUXT_PUBLIC_AUTH_MODE=cookie
```

## Tests

```powershell
cd backend
pip install ".[test]"
pytest
```

Contract tests do not need PostgreSQL. Runtime CRUD requires Compose.

Docker-only test and smoke verification:

```powershell
docker compose --env-file backend.env -f compose.backend.yml run --rm --no-deps api pytest -q
docker compose --env-file backend.env -f compose.backend.yml run --rm api python scripts/smoke.py
```

## Production operations

Create PostgreSQL and MinIO backups in the Docker volume `backend_backups`:

```powershell
docker compose --env-file backend.env.production -f compose.backend.yml --profile operations run --rm postgres-backup
docker compose --env-file backend.env.production -f compose.backend.yml --profile operations run --rm minio-backup
```

List and validate backup archives without copying database credentials to the host:

```powershell
docker run --rm -v docetra-backend_backend_backups:/backups postgres:17-alpine sh -c 'for f in /backups/*.dump; do pg_restore --list "$f" >/dev/null && echo "$f OK"; done'
```

Restore only during an approved recovery window, after taking a new backup. Replace `BACKUP_FILE` with the exact archive name:

```powershell
docker compose --env-file backend.env.production -f compose.backend.yml --profile operations run --rm --entrypoint sh postgres-backup -c 'pg_restore --clean --if-exists --no-owner --host=postgres --username="$PGUSER" --dbname="$PGDATABASE" "/backups/BACKUP_FILE.dump"'
```

Restore MinIO from the mirrored directory with an operations-profile `minio/mc` container after verifying the destination alias. Regularly copy or snapshot the `backend_backups` Docker volume to storage outside this host; a local volume alone does not protect against host loss.

## Notes

- Login uses a JWT in the HttpOnly `docetra_session` cookie plus `docetra_refresh`. CSRF uses `XSRF-TOKEN`. The JWT is never returned in JSON.
- Identity/org/record writes also persist to `roles`, `organizations`, `officers`, `records`, and `meeting_schedules`.
- Business collections still expose the Nuxt `/api/v2` URLs via the entity adapter.
- List filters: `page`, `limit`, `q`, `sort`, `status`, `stage`, `startDate`, `endDate`.
- Default lists hide `archived` and `deleted` unless `status` is passed (Archive workspace).
- Record/portal/system logs are read-only.
- Production: unique `SESSION_SECRET` / `JWT_SECRET`, `SESSION_COOKIE_SECURE=true`, CORS allow-list only.
- `/health`, `/ready`, and Prometheus-compatible `/metrics` support container health and monitoring.
- SMTP, Telegram, and Google Drive adapters are real integrations; their connection tests remain disabled until deployment credentials are supplied.
