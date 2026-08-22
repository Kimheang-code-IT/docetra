# Backend File Structure (FastAPI modular monolith)

This is the **implementation map** for the Docetra API. It exists so backend work can start from a known tree instead of inventing folders later.

**Status:** modular monolith (2026-08). Domain logic lives under nested `app/modules/<name>/{api,domain,services,repositories}/`. HTTP mounts from module `api/router.py` via `api/v2/router.py`. Reusable helpers live in `app/shared/`; infra in `core/`; vendor I/O in `integrations/`. URL prefix remains `/api/v2`. Persistence targets typed tables (`role`, `officer`, `organization`, `record`, `record_detail`, `file`, `setting`, `audit_log`); Entity JSONB remains only for portal drive-sync / storage-providers / export jobs until those paths are ported and `entities` is dropped.

**Authoritative contracts:**

| Source | Role |
| --- | --- |
| [`09-frontend-response-requirements.md`](./09-frontend-response-requirements.md) | Master response contract — every endpoint JSON shape |
| `frontend/app/utils/constants/api-endpoints.ts` | Exact `/api/v2` paths |
| `frontend/app/adapters/createEntityAdapter.ts` | Shared CRUD + lifecycle + comments/activity/attachments |
| `frontend/app/types/docetra/` | Response field names (camelCase) |
| `frontend/app/utils/role/permissions.ts` | Capability catalog |
| `prompt/specification/01-system-architecture.md` | Module boundaries |
| `prompt/specification/07-data-model.md` | PostgreSQL entities |
| This folder (`00`–`05`, `modules/*`) | Behavior, cache, scheduler, notifications |

When this file and `prompt/specification/` disagree on architecture, the specification wins. When this file and the frontend adapters disagree on a path or payload key, **the frontend adapter wins** until an explicit versioned API change is agreed.

---

## 1. Runtime processes (must match Compose)

`compose.backend.yml` runs one image three ways:

```text
api        → FastAPI / uvicorn on :8000          (uvicorn app.main:app)
worker     → python -m app.main worker           (RabbitMQ consumers)
scheduler  → python -m app.main scheduler        (APScheduler; publishes to RabbitMQ)

Do not start the scheduler or worker inside the API process — Compose still runs three containers; they share one entry module (`app.main`).
```

Do not start a scheduler inside the API process. Do not put long file scans, Drive sync, export generation, or notification delivery in an HTTP handler.

Local topology (already documented):

```text
Browser → Nuxt on host :3000 → Docker API :8000
                                 ├─ PostgreSQL 17
                                 ├─ Redis 8 (DB 0 ops, DB 1 short cache, DB 2 long cache)
                                 ├─ RabbitMQ 4
                                 └─ MinIO (S3-compatible)
```

---

## 2. Repository placement

Create the Python project at repo root as `backend/` (sibling of `frontend/`). Root Docker files stay where they are:

```text
bongLymeng/
  compose.backend.yml          # already exists
  backend.env.example          # already exists
  frontend/                    # Nuxt app (implemented)
  prompt/backend/              # these prompts
  backend/                     # FastAPI source — create in a later build task
```

The API image working directory is `backend/`. Dockerfile copies only that tree plus locked dependencies.

---

## 3. Target tree

Use this layout. Empty `__init__.py` files are implied for every Python package.

```text
backend/
  alembic/
  tests/
    conftest.py
    contract/
    integration/

  app/
    main.py                       # API (create_app) + worker + scheduler CLI
    jobs/                           # worker consumers + scheduler ticks
      publishers.py topology.py
      consumers/                    # RabbitMQ handlers (worker process)
      scheduler/                    # APScheduler ticks (scheduler process)
      deps.py
      router.py                    # mounts module routers + health/system
      entities.py
      endpoints/health.py system.py  # platform-only (not business modules)

    modules/<name>/                 # vertical slice per domain
      __init__.py                   # public façade
      api/router.py                 # FastAPI routes for this domain
      domain/                       # schemas, enums, constants, map, permissions
      services/                     # business logic
      repositories/                 # SQL helpers

    modules/
      record/
      organization/
      people_access/
      storage_integration/
      admin_config/
      reporting_support/

    shared/                         # reusable utils (2+ modules)
      pagination.py ids.py dicts.py responses.py
      datetime.py filters.py validators.py types.py
      schemas/common.py

    integrations/                   # outbound vendor clients only
      email/ telegram/ google/

    models/                         # ORM (shared; Alembic-safe)
    # (no top-level app/repositories — use modules/*/repositories + app.shared)
    # (no top-level app/schemas — use modules/*/domain/schemas or shared/schemas)

    core/                           # config, security, authz, cache, secrets
    db/                             # base.py session.py mixins.py
    jobs/                           # worker consumers + scheduler ticks
      publishers.py topology.py
      consumers/                    # RabbitMQ handlers (worker process)
      scheduler/                    # APScheduler ticks (scheduler process)
```

**Layer split**

| Layer | Owns |
| --- | --- |
| `core/` | Infra: config, JWT/CSRF, authz Depends, rate limit, cache, logging, secrets |
| `shared/` | Pure helpers: pagination, UUIDs, envelopes, deep_merge, common Pydantic |
| `integrations/` | SMTP, Telegram bot API, Google Drive client |
| `modules/*` | Feature API + domain + services + repositories |

Import convention: `from app.shared.pagination import parse_limit, page_meta, paginate`. Modules must not copy these helpers. Cross-module calls use the other package’s `__init__` façade.

---

## 4. Layer rules

```text
modules/<domain>/api/router.py
  → validate request, authn, CSRF, call services, return envelope
modules/<domain>/services/
  → business rules, permission re-check, transactions, outbox rows
modules/<domain>/repositories/ + shared/
  → SQL + pagination/ids
integrations/
  → vendor I/O only
models/ + db/
  → persistence only
jobs/
  → RabbitMQ consumers (worker) + APScheduler ticks (scheduler); idempotent; reload row before acting
```

- Routers do not query unrelated tables directly.
- Modules talk across domains through public package APIs, not ad-hoc SQL joins on foreign tables.
- `shared/` must not import `modules.*` or `integrations.*`.
- Cache writes happen **after** commit. Invalidation events go through the outbox.
- JSON field names match TypeScript (`recordTime`, `startDate`, `pageAccess`). Database columns stay snake_case (`record_time`, `start_date`).
- Prefer `from app.modules.<domain>…` and `from app.shared…`.

---

## 5. API router map (frontend → file)

All paths below are relative to `/api/v2`. Copy them from `frontend/app/utils/constants/api-endpoints.ts`; do not invent shorter aliases like `/records/incoming`.

**Record collections are dynamic** under `/records/{typeCode}` (plus `/records/_meta/surfaces`, `/records/logs`). Meeting board helpers live under `/records/meeting_history/*`. There is **no** `/meetings/*` HTTP family. Full contract: [`07-dynamic-record-collections.md`](./07-dynamic-record-collections.md).

**Organization collections are dynamic** under `/organizations/{orgType}` (`department` \| `company`) plus lookups `/sectors`, `/purposes`, `/officers`. Full contract: [`08-dynamic-organization-collections.md`](./08-dynamic-organization-collections.md).

### 5.1 Auth — `app/api/v2/auth.py` ← `frontend/app/adapters/auth.ts`

| Method | Path | Frontend |
| --- | --- | --- |
| POST | `/auth/login` | `AUTH_LOGIN` |
| POST | `/auth/logout` | `AUTH_LOGOUT` |
| GET | `/auth/me` | `AUTH_ME` |
| POST | `/auth/refresh` | `AUTH_REFRESH` |
| POST | `/auth/forgot-password` | `AUTH_FORGOT_PASSWORD` |
| POST | `/auth/forgot-password/verify` | `AUTH_RESET_VERIFY` |
| POST | `/auth/forgot-password/resend` | `AUTH_RESET_RESEND` |
| POST | `/auth/forgot-password/reset` | `AUTH_RESET_PASSWORD` |
| POST | `/auth/change-password` | `AUTH_CHANGE_PASSWORD` |
| PUT | `/auth/profile/avatar` | `AUTH_PROFILE_AVATAR` |
| DELETE | `/auth/profile/avatar` | `AUTH_PROFILE_AVATAR` |

Login returns `{ data: { user } }` and sets session + CSRF cookies. It does **not** return a session secret. Avatar accepts a safe raster payload (PNG/JPEG/WebP/GIF, max 2 MB) matching the profile dialog.

### 5.2 Shared entity surface — every collection router

`createEntityAdapter` is the default HTTP shape. Implement it once as a reusable router factory or mixin, then bind each resource.

For collection `{base}` (example `/records/incoming-documents`):

| Method | Path | Adapter method |
| --- | --- | --- |
| GET | `{base}` | `list` (`page`, `limit`, `q`, `sort`, `view`, `stage`, `status`, `startDate`, `endDate`, extra filters) |
| GET | `{base}/counts` | `getGroupCounts` (`groupBy`) |
| GET | `{base}/{id}` | `get` |
| POST | `{base}` | `create` |
| PATCH | `{base}/{id}` | `update` (optimistic `version`) |
| POST | `{base}/{id}/archive` | `archive` |
| POST | `{base}/{id}/restore` | `restore` |
| DELETE | `{base}/{id}` | `delete` (soft) |
| POST | `{base}/bulk-delete` | `deleteMany` |
| DELETE | `{base}/{id}/purge` | `purge` |
| PATCH | `{base}/{id}/stage` | `transitionStage` body `{ stage }` |
| GET/POST | `{base}/{id}/comments` | `listComments` / `addComment` |
| PATCH/DELETE | `{base}/{id}/comments/{commentId}` | `updateComment` / `deleteComment` |
| GET | `{base}/{id}/activity` | `listActivity` |
| GET/PUT | `{base}/{id}/attachments` | `listAttachments` / `replaceAttachments` |
| GET | `{base}/{id}/neighbors` | `getNeighbors` |
| GET/PUT | `{base}/{id}/favorite` | `getFavorite` / `setFavorite` |
| GET | `{base}/options` | `loadReferenceOptions` (`q`, `limit`, `status`, `valueField`, `hierarchy`, `excludeId`) |

Default list filter excludes `archived` and `deleted` unless `status` is passed. Archive UI today calls each source twice (`status=archived` and `status=deleted`); that must work before any aggregate `/archive` endpoint is added.

### 5.3 Resource bases

| Router file | Base path | Frontend adapter key |
| --- | --- | --- |
| `dynamic_records.py` | `/records/{typeCode}` (+ schema, board helpers, comments, attachments) | `createRecordAdapter(typeCode)` |
| `records.py` | mounts dynamic router only (`/records/logs`, `/_meta/surfaces` included there) | — |
| `organizations.py` | lookups `/sectors`, `/purposes`, `/officers` + dynamic `/organizations/{orgType}` | dynamic org |
| `users.py` | `/users/roles` | `roles` |
| `users.py` | `/users` | `users` |
| `users.py` | `/users/permission-catalog` | role matrix catalog |
| `configuration.py` | `/configuration/record-types` | `recordTypes` |
| `configuration.py` | `/configuration/record-attributes` | `recordAttributes` |
| `portal.py` | `/portal/file-uploads` | `fileUploads` |
| `portal.py` | `/portal/google-drive-sync` | `googleDriveSync` |
| `portal.py` | `/portal/logs` | `portalLogs` |
| `system.py` | `/system/logs` | `systemLogs` |

### 5.4 Meeting extras — `meetings.py` ← `frontend/app/adapters/meeting-board.ts`

| Method | Path | Constant |
| --- | --- | --- |
| POST | `/records/meeting_history/reorder` | `MEETINGS_REORDER` |
| POST | `/records/meeting_history/{id}/assign-topic` | `MEETING_ASSIGN_TOPIC` |
| POST | `/records/meeting_history/{id}/attachments/link` | `MEETING_ATTACHMENTS_LINK` |
| GET/POST | `/records/meeting_history/{id}/attachments` | `MEETING_ATTACHMENTS` |
| GET | `/portal/drive-files` | `PORTAL_DRIVE_FILES` |

After meeting writes commit, upsert or remove APScheduler jobs (`02-meeting-scheduler.md`).

### 5.5 Settings — `settings.py` ← `frontend/app/repositories/http/`

| Method | Path | Constant |
| --- | --- | --- |
| GET/PUT | `/settings/app-info` | `APP_INFO` |
| POST | `/settings/app-info/reset` | `APP_INFO_RESET` |
| GET/PATCH | `/settings/app-config` | `APP_CONFIG` |
| POST | `/settings/app-config/email/test-connection` | `APP_CONFIG_TEST_EMAIL` |
| POST | `/settings/app-config/email/send-test` | `APP_CONFIG_SEND_TEST_EMAIL` |
| POST | `/settings/app-config/telegram/test-connection` | `APP_CONFIG_TEST_TELEGRAM` |
| POST | `/settings/app-config/telegram/send-test` | `APP_CONFIG_SEND_TEST_TELEGRAM` |
| GET/POST | `/settings/storage` | `STORAGE_PROVIDERS` |
| GET/PATCH/DELETE | `/settings/storage/{id}` | `STORAGE_PROVIDER` |
| POST | `/settings/storage/{id}/test-connection` | `STORAGE_PROVIDER_TEST` |
| POST | `/settings/storage/{id}/set-default` | `STORAGE_PROVIDER_SET_DEFAULT` |
| POST | `/settings/storage/{id}/set-active` | `STORAGE_PROVIDER_SET_ACTIVE` |

### 5.6 Cross-cutting

| Router | Path | Frontend |
| --- | --- | --- |
| `dashboard.py` | GET `/dashboard/summary` | `fetchDashboardSummary` |
| `search.py` | GET `/search` (`q`, `mode`, `limit`) | `searchKeyword` / `searchSemantic` |
| `search.py` | POST `/search/ask` | `askAi` |
| `exports.py` | POST `/exports` then poll GET `/exports/{id}` | `createExportJob` → `202` + job |
| `mentions.py` | GET `/mentions` (`q`, `type`, `limit`) | `AppMentionMultiInput` option search |

Mention `type` is `officer` | `department` | `company`. Response items are `{ id, label, type }`.

---

## 6. Permission catalog (must match UI matrix)

Source: `frontend/app/utils/role/permissions.ts`.

Flat keys: `{permissionPrefix}.{action}`.

| Prefix | Typical actions |
| --- | --- |
| `dashboard` | view |
| `archive` | view |
| `records.incoming_documents` | workflow set |
| `records.outgoing_documents` | workflow set |
| `records.documents` | workflow set |
| `records.master_list_requests` | workflow set |
| `records.meeting_topic` | workflow set |
| `records.meeting_history` | workflow set |
| `organizations.departments` | master-data set |
| `organizations.companies` | master-data set |
| `organizations.purposes` | master-data set |
| `organizations.sectors` | master-data set |
| `organizations.officers` | master-data set |
| `users.users` | view/create/edit/archive/restore/delete/purge/comment/configure |
| `users.roles` | same as users |
| `configuration.record_types` | config set |
| `configuration.record_attributes` | config set |
| `records.logs` | view, export |
| `portal.file_upload` | view, create, delete, share, export |
| `portal.google_drive_sync` | config set |
| `portal.logs` | view, export |
| `system.logs` | view, export |
| `settings.app_config` | view, edit, configure |
| `settings.app_info` | view, edit, configure |
| `settings.storage` | view, edit, configure |

Workflow actions: `view create edit archive restore delete purge assign share export comment transition`.

`GET /users/permission-catalog` returns the same matrix rows the role editor expects (`documentType`, allowed `actions`). `ALL_PAGES` is reserved for a trusted super-admin policy.

`/auth/me` returns `permissions` (flat keys) and may also return `pageAccess` for compatibility.

---

## 7. Database files vs product tables

Keep SQLAlchemy models aligned with `prompt/specification/07-data-model.md`. Suggested grouping:

| File | Tables |
| --- | --- |
| `models/record.py` | `record`, `record_detail`, `record_attachment`, `record_organization`, `record_stage_template` |
| `models/configuration.py` | `setting`, `enum` (app settings); record types live in `models/record.py` |
| `models/organization.py` | `organization` (dept/company), `organization_sector`, `organization_purpose` |
| `models/people.py` | `officer`, `users`, `role`, `permission`, `role_permission`, `menu` |
| `models/storage.py` | `file`, Drive sync source/job |
| `models/audit.py` | activity, comments, system/portal/record logs |
| `models/jobs.py` | export jobs, outbox, RabbitMQ delivery receipts |
| `models/scheduler.py` | APScheduler job store + meeting schedule mapping |

Shared mixin fields: `id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `version`, and lifecycle `status` where the product uses `active | archived | deleted`.

`record_time` is configurable (see record-type `recordTimePriority`). Index it. List/board date filters use `startDate`/`endDate` against the resolved business time, not `created_at` alone. Details: [`07-datetime-and-list-query.md`](./07-datetime-and-list-query.md).

---

## 8. Frontend type → Pydantic schema

Keep one schema file per frontend type module:

| Frontend type | Backend schema |
| --- | --- |
| `types/docetra/common.ts` | `shared/schemas/common.py` (`ApiResponse`, `ListQuery`, comments, activity, attachments) |
| `types/docetra/entities.ts` | `modules/*/domain/schemas.py` (record, meeting, organization, user) |
| `types/docetra/export.ts` | `modules/reporting_support/domain/schemas.py` |
| `types/docetra/search.ts` | `modules/reporting_support/domain/schemas.py` |
| `types/docetra/settings.ts` | `modules/admin_config/domain/schemas.py` |
| `types/auth-user.ts` | `modules/people_access/domain/schemas.py` (`AuthUser`) |

Do not keep a top-level `app/schemas/` package; import from module domain or shared.

Do not leak password hashes, session ids, storage secrets, or Telegram/SMTP tokens in any GET schema.

---

## 9. Tests that must exist before HTTP cutover

```text
tests/unit/modules/<domain>/    # per-module pure unit tests
tests/unit/core/ + security/    # JWT, secrets, authz, production config
tests/unit/shared/              # pagination / envelopes
tests/contract/                 # OpenAPI paths + frontend envelope shapes
tests/integration/              # live Docker API (marker: integration)
tests/integration/modules/      # per-module smoke
tests/integration/test_modules_together.py
```

See [`backend/tests/README.md`](../../backend/tests/README.md). Default `pytest` skips integration.

Frontend still typechecks against its adapters. Changing a path requires a paired frontend adapter change.

---

## 10. First-create checklist (later build task)

When a later task is allowed to create `backend/` source:

1. Scaffold `pyproject.toml`, Dockerfile, Alembic, `app/main.py` (API + worker + scheduler CLI).
2. Implement `core/` (config, errors, session, CSRF, permissions, datetime).
3. Health endpoints + OpenAPI at `/api/v2/openapi.json`.
4. Auth + `/auth/me` so Nuxt can set `NUXT_PUBLIC_USE_MOCK_DATA=false`.
5. One entity (departments) through the full adapter surface, then copy the pattern.
6. Follow [`08-implementation-sequence.md`](./08-implementation-sequence.md) so work matches the delivery timeline.

Until then, keep this file as the only backend tree source of truth.
