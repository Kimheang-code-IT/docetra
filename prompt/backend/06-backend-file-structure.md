# Backend File Structure (FastAPI modular monolith)

This is the **implementation map** for the Docetra API. It exists so backend work can start from a known tree instead of inventing folders later.

**Status:** implemented. The Python `backend/` package follows this map and builds image `docetra-backend:local` with three process entrypoints.

**Authoritative contracts:**

| Source | Role |
| --- | --- |
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
api        → FastAPI / uvicorn on :8000          (app.main)
worker     → python -m app.worker                (RabbitMQ consumers)
scheduler  → python -m app.scheduler             (APScheduler; publishes to RabbitMQ)
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
  pyproject.toml
  uv.lock | poetry.lock | pdm.lock     # one lockfile; pin FastAPI, SQLAlchemy, Alembic, APScheduler
  Dockerfile
  .dockerignore
  alembic.ini
  README.md                            # how to run api / worker / scheduler locally

  alembic/
    env.py
    versions/                          # one migration per domain change

  tests/
    conftest.py
    contract/                          # OpenAPI vs frontend ApiEndpoints
    api/
    modules/
    jobs/
    permissions/

  app/
    __init__.py
    main.py                            # create_app(); mounts /api/v2
    worker.py                          # python -m app.worker
    scheduler.py                       # python -m app.scheduler

    api/
      v2/
        __init__.py
        router.py                      # include_router for every family below
        deps.py                        # current user, CSRF, db session, idempotency
        health.py                      # GET /health, GET /ready (not under /api/v2 if preferred)
        auth.py
        dashboard.py
        meetings.py
        records.py
        organizations.py
        users.py
        configuration.py
        settings.py
        portal.py
        system.py
        search.py
        exports.py
        mentions.py                    # assignment typeahead (officer/department/company)

    core/
      config.py                        # pydantic-settings from backend.env
      security.py                      # password hashing, JWT cookies, CSRF
      jwt.py                           # encode/decode access+refresh JWT
      csrf.py
      cors.py
      errors.py                        # { error: { code, message, fields, requestId } }
      logging.py
      permissions.py                   # catalog from ROLE_DOCUMENT_TYPES
      pagination.py                    # page/limit/sort; cap "All"
      datetime.py                      # UTC store, ISO serialize, range filters
      cache.py                         # short/long Redis tiers
      messaging.py                     # RabbitMQ publish with confirms
      outbox.py                        # transactional outbox with the DB commit
      ids.py                           # UUID/ULID generation

    db/
      jwt.py
      base.py
      mixins.py                        # id, timestamps, created_by, updated_by, version, status

    models/                            # SQLAlchemy tables (snake_case columns)
      record.py
      organization.py
      people.py
      storage.py
      configuration.py
      audit.py
      jobs.py
      scheduler.py

    schemas/                           # Pydantic v2; API aliases = frontend camelCase
      common.py                        # envelopes, ListQuery, PersonSummary, AssignmentRef
      auth.py
      record.py
      meeting.py
      organization.py
      user.py
      configuration.py
      settings.py
      portal.py
      search.py
      export.py

    modules/                           # application services — no FastAPI imports here
      identity/                        # login, session, password reset, avatar
      people_access/                   # users, roles, permission catalog
      organization/                    # depts, companies, purposes, sectors, officers
      admin_config/                    # record types, attributes, app info/config
      record/                          # unified record + stages + details + boards
      meetings/                        # topic board, reorder, assign, notes, schedule upsert
      storage_integration/             # files, S3/MinIO, Drive sync jobs
      reporting_support/               # dashboard, exports, search projections
      notifications/                   # email + Telegram bot adapters
      collaboration/                   # comments, activity, attachments, favorites, neighbors

    jobs/
      topology.py                      # exchange/queue/routing-key names
      publishers.py
      consumers/
        files.py
        drive.py
        exports.py
        notifications.py
        search_index.py
        cache_invalidation.py
        meeting_events.py
        recurrence.py

    scheduler_jobs/
      meeting_reminders.py
      meeting_start_end.py
      recurrence_horizon.py
      reconcile.py
      cleanup.py
```

---

## 4. Layer rules

```text
api/v2/*.py
  → validate request, authn, CSRF, call a module service, return envelope
modules/*/
  → business rules, permission re-check, transactions, outbox rows
models/ + db/
  → persistence only
jobs/ + scheduler_jobs/
  → side effects after commit; idempotent; reload entity before acting
```

- Routers do not query other modules' tables.
- Services talk across modules through explicit interfaces (Python protocols), not ad-hoc SQL joins on foreign tables.
- Cache writes happen **after** commit. Invalidation events go through the outbox.
- JSON field names match TypeScript (`recordTime`, `startDate`, `pageAccess`). Database columns stay snake_case (`record_time`, `start_date`).

---

## 5. API router map (frontend → file)

All paths below are relative to `/api/v2`. Copy them from `frontend/app/utils/constants/api-endpoints.ts`; do not invent shorter aliases like `/records/incoming`.

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
| `meetings.py` | `/meetings/topics` | `meetingTopics` |
| `meetings.py` | `/meetings/history` | `meetingHistory` |
| `records.py` | `/records/incoming-documents` | `incomingDocuments` |
| `records.py` | `/records/outgoing-documents` | `outgoingDocuments` |
| `records.py` | `/records/documents` | `documents` |
| `records.py` | `/records/master-list-requests` | `masterListRequests` |
| `records.py` | `/records/logs` | `recordLogs` (read-only; no create) |
| `organizations.py` | `/organizations/departments` | `departments` |
| `organizations.py` | `/organizations/companies` | `companies` |
| `organizations.py` | `/organizations/company-purposes` | `companyPurposes` |
| `organizations.py` | `/organizations/company-sectors` | `companySectors` |
| `organizations.py` | `/organizations/officers` | `officers` |
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
| POST | `/meetings/reorder` | `MEETINGS_REORDER` |
| POST | `/meetings/history/{id}/assign-topic` | `MEETING_ASSIGN_TOPIC` |
| POST | `/meetings/history/{id}/attachments/link` | `MEETING_ATTACHMENTS_LINK` |
| GET/POST | `/meetings/history/{id}/attachments` | `MEETING_ATTACHMENTS` |
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
| `meetings.topics` | workflow set |
| `meetings.history` | workflow set |
| `organizations.departments` | master-data set |
| `organizations.companies` | master-data set |
| `organizations.company_purposes` | master-data set |
| `organizations.company_sectors` | master-data set |
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
| `models/configuration.py` | `record_type`, `record_attribute`, `record_template`, `setting`, `document_type` |
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
| `types/docetra/common.ts` | `schemas/common.py` (`ApiResponse`, `ListQuery`, comments, activity, attachments) |
| `types/docetra/entities.ts` | `schemas/record.py`, `meeting.py`, `organization.py`, `user.py` |
| `types/docetra/export.ts` | `schemas/export.py` |
| `types/docetra/search.ts` | `schemas/search.py` |
| `types/docetra/settings.ts` | `schemas/settings.py` |
| `types/auth-user.ts` | `schemas/auth.py` (`AuthUser`) |

Do not leak password hashes, session ids, storage secrets, or Telegram/SMTP tokens in any GET schema.

---

## 9. Tests that must exist before HTTP cutover

```text
tests/contract/test_api_paths.py     # every ApiEndpoints constant is routed
tests/api/test_envelopes.py          # data/meta/error shapes
tests/api/test_session_csrf.py
tests/permissions/test_capability_matrix.py
tests/modules/test_lifecycle.py      # archive/restore/delete/purge
tests/jobs/test_idempotent_retry.py
tests/modules/test_datetime_filters.py
```

Frontend still typechecks against its adapters. Changing a path requires a paired frontend adapter change.

---

## 10. First-create checklist (later build task)

When a later task is allowed to create `backend/` source:

1. Scaffold `pyproject.toml`, Dockerfile, Alembic, `app/main.py`, `app/worker.py`, `app/scheduler.py`.
2. Implement `core/` (config, errors, session, CSRF, permissions, datetime).
3. Health endpoints + OpenAPI at `/api/v2/openapi.json`.
4. Auth + `/auth/me` so Nuxt can set `NUXT_PUBLIC_USE_MOCK_DATA=false`.
5. One entity (departments) through the full adapter surface, then copy the pattern.
6. Follow [`08-implementation-sequence.md`](./08-implementation-sequence.md) so work matches the delivery timeline.

Until then, keep this file as the only backend tree source of truth.
