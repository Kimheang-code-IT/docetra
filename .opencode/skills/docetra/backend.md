# Backend

Map: `prompt/backend/06-backend-file-structure.md`. Spec: `prompt/specification/01-system-architecture.md`, `08-shared-standards.md`. Response JSON: `prompt/backend/09-frontend-response-requirements.md`.

When this map and `prompt/specification/` disagree on architecture, **specification wins**. When this map and frontend adapters disagree on path or payload key, **frontend adapter wins** until a versioned API change.

## Processes (Compose)

| Process | Entry |
| --- | --- |
| API | `uvicorn app.main:app` `:8000` |
| Worker | `python -m app.main worker` |
| Scheduler | `python -m app.main scheduler` (UTC, Postgres job store) |

Do not start worker or scheduler inside the API process. HTTP handlers must not do Drive sync, large exports, file scans, or notification delivery — publish to RabbitMQ.

## Modules

`backend/app/modules/<name>/{api,domain,services,repositories}/`

- `record` — unified records, types, stages, details, comments, activity, attachments
- `organization` — department/company and related org collections
- `people_access` — officers, users, roles, permissions, session
- `storage_integration` — files, Drive, providers
- `admin_config` — record types/attributes, settings
- `reporting_support` — dashboard, search, exports

HTTP mounts from module `api/router.py` via `api/v2/router.py`. Prefix `/api/v2`.

Shared: `app/shared/`. Infra: `core/`. Vendor I/O: `integrations/`.

## Data

Typed tables: `role`, `officer`, `organization`, `record`, `record_detail`, `file`, `setting`, `audit_log`. Entity JSONB remains only for portal drive-sync / storage-providers / export jobs until ported.

Dynamic collections: `/api/v2/records/{typeCode}`, `/api/v2/organizations/{orgType}`. See `prompt/backend/07-dynamic-record-collections.md`.

## Cache and async

Redis: DB 0 ops/session, DB 1 short cache, DB 2 long cache. Tenant- and permission-scoped keys, TTL required. PostgreSQL remains authorization and business truth. Invalidation after commit. Spec: `prompt/backend/01-cache-and-messaging.md`.

## API rules

- Enforce permission on the server. Do not trust the client.
- Validate at the HTTP boundary; re-check business rules in services.
- Stable error categories; no stack traces to clients.
- Optimistic concurrency on writes (`version` / `If-Match`).
- Audit significant actions (actor, action, target, time).

## Tests

From `backend/`: `python -m pytest -q` (unit + contract). Integration needs Compose: `python -m pytest tests/integration -m integration -q`. Layout: `backend/tests/README.md`.
