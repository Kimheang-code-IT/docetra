# Docetra backend

FastAPI API, RabbitMQ worker, and APScheduler jobs (separate process by default, or in-API when `SCHEDULER_IN_API=true`). Matches the Nuxt adapters in `frontend/app/utils/constants/api-endpoints.ts`.

## Processes

| Command | Role |
| --- | --- |
| `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000` | HTTP API |
| `python -m app.main worker` | Outbox publisher, export completion, queue consumers |
| `python -m app.main scheduler` | UTC meeting reminder / reconcile ticks (or set `SCHEDULER_IN_API=true` on the API for small deploys) |
| `python -m app.main telegram` | Dedicated Telegram bot long-polling process (menus, range filters) |

### Small team (~20 users) — keep all three

User count does **not** justify folding RabbitMQ work into FastAPI. Even on one VPS, run:

```text
1× api | 1× worker | 1× scheduler | 1× postgres | 1× redis | 1× rabbitmq | 1× minio
```

Tuned defaults in `infrastructure/.env.example`:

| Setting | Small default | Notes |
| --- | --- | --- |
| `WORKER_CONCURRENCY` | `2` | Cap in-flight handlers |
| `WORKER_PREFETCH` | `2` | RabbitMQ QoS; keep low until lag appears |
| `SCHEDULER_*` | UTC + 15m reconcile / 1m reminders | Scheduler only **publishes**; workers execute |

HTTP handlers publish jobs (Drive sync, exports, notifications, scans). Workers consume them. APScheduler never delivers Telegram/email itself.

## Tests

See [`tests/README.md`](tests/README.md).

```powershell
python -m pytest -q                                          # unit + contract
python -m pytest tests/unit/modules -q                       # all modules
python -m pytest tests/unit/security -q                      # security helpers
python -m pytest tests/integration -m integration -q         # needs Docker API
```


From the repository root:

```powershell
Copy-Item infrastructure/.env.example infrastructure/.env
docker compose -f infrastructure/docker-compose.yml up --build -d
```

Default path: an empty database shows **Create administrator** on `/auth/login`. The first registered user becomes SuperAdmin with every permission. No user is ever seeded automatically — accounts are inserted only through the backend (`POST /api/v2/auth/register` for the first administrator, then the users API).

Generate independent secrets without installing tooling on the host:

```powershell
docker run --rm python:3.12-slim python -c "import secrets; [print(secrets.token_urlsafe(48)) for _ in range(6)]"
```

Copy the template to `infrastructure/.env.production`, fill in every `CHANGE_ME`, then start with:

```powershell
docker compose --env-file infrastructure/.env.production -f infrastructure/docker-compose.yml up --build -d
```

Local and production templates use different `DOCETRA_COMPOSE_PROJECT` values. Keep them different: PostgreSQL, RabbitMQ, Redis, MinIO, and backup volumes must never be shared between environments. If an environment file is changed, recreate containers with that same file instead of using `docker compose restart`.

Point Nuxt at the API (empty base = same-origin `/api/v2` proxy):

```env
NUXT_PUBLIC_API_BASE=
NUXT_API_PROXY_TARGET=http://127.0.0.1:8000
NUXT_PUBLIC_AUTH_MODE=cookie
```

## Tests

```powershell
cd backend
pip install ".[test]"
pytest
```

Contract tests do not need PostgreSQL. Runtime CRUD requires Compose.

The production API image does not include tests or scripts. Run them on the host against the Compose API:

```powershell
cd backend
pip install ".[test]"
python -m pytest -q
python -m pytest tests/integration -m integration -q
```

## Production operations

Create PostgreSQL and MinIO backups in the Docker volume `backend_backups`:

```powershell
docker compose --env-file infrastructure/.env.production -f infrastructure/docker-compose.yml --profile operations run --rm postgres-backup
docker compose --env-file infrastructure/.env.production -f infrastructure/docker-compose.yml --profile operations run --rm minio-backup
```

List and validate backup archives without copying database credentials to the host:

```powershell
docker run --rm -v docetra-backend_backend_backups:/backups postgres:17-alpine sh -c 'for f in /backups/*.dump; do pg_restore --list "$f" >/dev/null && echo "$f OK"; done'
```

Restore only during an approved recovery window, after taking a new backup. Replace `BACKUP_FILE` with the exact archive name:

```powershell
docker compose --env-file infrastructure/.env.production -f infrastructure/docker-compose.yml --profile operations run --rm --entrypoint sh postgres-backup -c 'pg_restore --clean --if-exists --no-owner --host=postgres --username="$PGUSER" --dbname="$PGDATABASE" "/backups/BACKUP_FILE.dump"'
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
