# Local frontend with Docker backend

The Nuxt frontend runs directly on the developer computer at `http://localhost:3000`. The FastAPI API, APScheduler process, worker, PostgreSQL, Redis, RabbitMQ, and local object storage run in Docker. Only the API and optional MinIO/RabbitMQ administration consoles bind to `127.0.0.1`; databases, cache, scheduler, and broker traffic stay on Docker's private network.

## Current repository boundary

This repository does not yet contain the FastAPI source or a built backend image. `compose.backend.yml` defines the required runtime boundary and expects an image named `docetra-backend:local` by default. Build or load that image from the backend repository before starting the stack. The image must provide the API entrypoint, `python -m app.worker`, and `python -m app.scheduler`; override the latter commands with `BACKEND_WORKER_COMMAND` and `BACKEND_SCHEDULER_COMMAND` when necessary.

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
# Set NUXT_PUBLIC_USE_MOCK_DATA=false in .env.
pnpm install
pnpm dev
```

The browser calls `http://localhost:8000/api/v2`. The API must allow exactly `http://localhost:3000`, enable credentialed CORS, and never combine credentials with `Access-Control-Allow-Origin: *`.

RabbitMQ management is available locally at `http://localhost:15672` with the local credentials in `backend.env`. MinIO administration remains at `http://localhost:9001`. Neither console is exposed publicly in production.

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
