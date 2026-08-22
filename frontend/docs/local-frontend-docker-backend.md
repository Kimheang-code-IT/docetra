# Local frontend with Docker backend

The Nuxt frontend runs directly on the developer computer at `http://localhost:3000`. The FastAPI API, APScheduler process, worker, PostgreSQL, Redis, RabbitMQ, and local object storage run in Docker.

For local development, loopback-only ports are published so host tools can connect (DBeaver, Redis UI, MinIO/RabbitMQ consoles). Infra services attach to both `edge` (published ports) and `private` (container DNS). Worker/scheduler stay on `private` only.

## Current repository boundary

This repository includes the FastAPI source in `backend/` and image `docetra-backend:local`. `compose.backend.yml` builds that image and runs the API (`uvicorn app.main:app`), `python -m app.main worker`, and `python -m app.main scheduler`.

## Local startup

From the repository root:

```powershell
Copy-Item backend.env.example backend.env
# Generate and set SESSION_SECRET and PASSWORD_RESET_SECRET in backend.env.
$env:DOCETRA_BACKEND_IMAGE = 'docetra-backend:local'
docker compose --env-file backend.env -f compose.backend.yml up -d
```

Then configure and run the frontend:

```powershell
Set-Location frontend
Copy-Item .env.example .env
# Keep NUXT_PUBLIC_API_BASE empty (same-origin `/api/v2` proxy) and NUXT_PUBLIC_AUTH_MODE=cookie.
# NUXT_API_PROXY_TARGET=http://127.0.0.1:8000 is the FastAPI origin behind the proxy.
pnpm install
pnpm dev
```

The browser calls `http://localhost:3000/api/v2`. Nuxt (dev server or Node preview) proxies that to FastAPI on `:8000`, so the HttpOnly session cookie belongs to the UI origin. Playwright uses the same path (`PLAYWRIGHT_BASE_URL=http://localhost:3000`).

If the API is hosted on a different origin, set `NUXT_PUBLIC_API_BASE` to that origin (no `/api/v2` suffix). The API must then allow the UI origin, enable credentialed CORS, and never combine credentials with `Access-Control-Allow-Origin: *`.

### Local admin / tooling URLs (loopback only)

| Tool | URL / host | Credentials / notes |
| --- | --- | --- |
| API | `http://localhost:8000` | Health: `/health` |
| PostgreSQL (DBeaver) | `localhost:${POSTGRES_PORT:-5432}` | DB/user/password from `backend.env` (`POSTGRES_*`, defaults `docetra` / `docetra_local_only`) |
| Redis CLI / clients | `localhost:${REDIS_PORT:-6379}` | No password in local Compose |
| Redis browser UI | `http://localhost:8081` | Preloaded: **ops** (DB 0), **short** (DB 1), **long** (DB 2) |
| RabbitMQ management | `http://localhost:15672` | `RABBITMQ_USER` / `RABBITMQ_PASSWORD` from `backend.env` |
| MinIO API | `http://localhost:9000` | `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` |
| MinIO console | `http://localhost:9001` | Same MinIO credentials |

#### DBeaver → PostgreSQL

1. New connection → PostgreSQL.
2. Host `localhost`, port `5432` (or `POSTGRES_PORT`).
3. Database / user / password: values from `backend.env` (see table above).
4. Test connection, then finish.

Do not expose these ports beyond `127.0.0.1` in production.

## Cache and background work

- Redis DB 0 is operational state, DB 1 is the short cache tier, and DB 2 is the long cache tier.
- Short cache defaults to 30 seconds for changing board/list/count/typeahead reads.
- Long cache defaults to one hour, with resource-specific shorter TTLs for configuration, permissions, and schemas.
- RabbitMQ carries durable jobs for files, Drive sync, exports, notifications, search indexing, and cache invalidation.
- APScheduler stores meeting schedules persistently, runs in UTC, and publishes due reminder/recurrence/start/end work to RabbitMQ.
- Optional external delivery uses separate Meeting and Development Telegram bot secrets plus a third-party email adapter; leave all provider secrets blank/disabled until local credentials are configured.
- The worker processes messages with acknowledgements, idempotency, bounded retries, and dead-letter handling.
- PostgreSQL remains authoritative. See `prompt/backend/01-cache-and-messaging.md` and `prompt/backend/02-meeting-scheduler.md`.

## Required session contract

- Login sets a random, rotated session identifier in an `HttpOnly` cookie and returns `{ "data": { "user": { ... } } }`. A bearer token is not required in cookie mode.
- `/api/v2/auth/me` returns the current sanitized user and permission snapshot.
- `/api/v2/auth/logout` invalidates the server session and expires the cookie.
- Local cookies use `SameSite=Lax`, `Secure=false`, and host `localhost`. Production cookies use `Secure=true`, `HttpOnly=true`, a narrow path/domain, and an appropriate `SameSite` policy.
- The API sets a readable `XSRF-TOKEN` double-submit cookie and verifies `X-CSRF-Token` on every POST, PUT, PATCH, and DELETE request. It must also validate `Origin`/`Referer` for browser mutations.
- Rotate the session after login, password change, privilege change, and other security-sensitive transitions. Apply idle and absolute expiration server-side.

## Testing (backend → frontend)

```powershell
# Unit + OpenAPI contract (no Docker required)
Set-Location backend
python -m pytest -q

# Live API integration against Docker Compose API on :8000
python -m pytest tests/integration -m integration -q

# Frontend unit (Vitest) + browser smoke (Playwright; Nuxt must be on :3000)
Set-Location ..\frontend
pnpm test:unit
pnpm test:e2e
```

Prerequisites for live/E2E: `docker compose --env-file backend.env -f compose.backend.yml up -d` until `http://localhost:8000/ready` is OK, and `pnpm dev` (or preview) for Playwright.

Default admin: `admin@gmail.com` / `123456` (from `backend.env`).

## Production requirements

- Terminate TLS before both frontend and API; never send session cookies over HTTP.
- Store secrets in the deployment platform or Docker secrets, not Compose environment files.
- Pin container image versions/digests after backend implementation; do not deploy floating `latest` tags.
- Run the API as a non-root user in its image, keep the filesystem read-only, drop Linux capabilities, and expose only the reverse proxy publicly.
- Use independent production PostgreSQL/Redis/RabbitMQ/object-storage credentials, encrypted backups, health checks, resource limits, structured audit logs, and monitoring.
- Use managed or independently isolated Redis operational/cache workloads when eviction or failure isolation requires it. Use durable RabbitMQ quorum queues, publisher confirms, dead-letter queues, private networking, and TLS.
- Run APScheduler as a dedicated process with persistent PostgreSQL storage, a unique identity, UTC clock synchronization, monitored heartbeat/misfires, and tested restart recovery.
- Enforce authorization and record scope in FastAPI on every request. Frontend permission checks are presentation only.

The backend's environment variable names may be mapped to its settings model, but the security behavior above is mandatory.
