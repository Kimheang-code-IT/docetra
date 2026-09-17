# Docetra — Backend

FastAPI async application in `backend/app/`. All business endpoints are prefixed `/api/v2`.

## Entry points

- **API**: `uvicorn app.main:app` — HTTP only, never runs jobs.
- **Worker**: `python -m app.main worker` — RabbitMQ consumers (exports, outbox).
- **Scheduler**: `python -m app.main scheduler` — APScheduler: `cleanup_expired_exports`, `due_meeting_reminders`, `reconcile`. Small single-box deploys can set `SCHEDULER_IN_API=true` to run it inside the API.

## Telegram notifications

Meeting reminders flow: `meeting_schedules` → `due_meeting_reminders` publishes `meeting.reminder.due` → worker `handle_meeting_message` → `app/integrations/telegram` `sendMessage` to every enabled destination with a `chatId`.

- Token resolution: Settings → App Config → Telegram `botToken` (encrypted at rest) overrides the `TELEGRAM_MEETING_BOT_TOKEN` env fallback. `telegram.enabled` gates delivery.
- Config API (`settings.app_config.configure`): `POST /api/v2/settings/app-config/telegram/test-connection` (getMe + persist status), `POST .../telegram/send-test` (sends a real message to `chatId`/`destinationId` or all enabled destinations, marks them verified), `POST .../telegram/discover-chats` (getUpdates — returns chats that messaged the bot).
- **Telegram limitation**: a bot cannot start a chat. The user must open the bot in Telegram and press **Start** before messages deliver; `discover-chats` then returns that chat ID.

### Interactive bot (long polling)

A **dedicated process/container** long-polls the Bot API (`python -m app.main telegram`, gated by `TELEGRAM_BOT_POLLING`) and answers a button menu:

- **Main menu**: 📅 Meetings · 📄 Documents · 🏢 Departments · 👤 Officers.
- **Stepped flow on the reply keyboard** (buttons above the input):
  - Meetings → period (Today / Week / Month / All) or **📅 Custom range** → result
  - Documents → document type → period / custom range → result
  - Departments / Officers → result directly
- **Custom range**: send two dates, e.g. `01/09/2026 17/09/2026` (DD/MM/YYYY or YYYY-MM-DD); the end day is inclusive.
- The interactive menu is **private-chat only** — each user gets their own result messages. Groups are broadcast-only.
- Step changes post a short label message (sent quietly) that carries the next keyboard; the final result carries the main keyboard back.
- Every result ends with a `🕒 <time> UTC` footer.
- Only chats that are configured destinations or listed in `TELEGRAM_MEETING_ALLOWED_CHAT_IDS` are answered.
- Seen chats are cached in Redis (`telegram:known-chats`); per-chat flow state is in `telegram:bot:state:<chat>`.
- **Meeting alerts** are pushed by the worker to every enabled destination, including groups (all members see them).
- **Password-reset codes** are delivered by the worker to **private destinations only** — never groups/channels.

Run the bot only in the single `telegram` container/process.

## Layering rules (enforced by architecture tests)

```
Router → Application Workflow / Service → Repository → Database
Service → Service (cross-module, public facades only)
```

- Cross-module imports use only public `service`, `schema`, `exceptions` facades.
- `core`, `shared`, `integrations`, `platform` import no business modules.
- Services own rules but never commit; repositories own SQL/flush; routers/workflows own transactions.
- Approved dependency DAG: `reporting_support → record, organization, people_access, storage_integration`; `storage_integration → record, admin_config`; `record → organization, people_access, admin_config`; `organization → admin_config`; `people_access → admin_config`; `admin_config → none`.
- Platform audit/messaging is the only way to touch audit/outbox tables.

## Request lifecycle

1. **Middleware/CORS/session** — cookies parsed (`docetra_session`, `docetra_refresh`), CSRF header check (`X-CSRF-Token`).
2. **`current_user`** dependency (`core/security.py`) — validates JWT access token, loads `User`, builds `AuthUser` with permission set.
3. **Authorization** — `core/authorization.py: require_permission(user, key)`; resource routers derive the action from method + path suffix (`_action_from_request`: GET→view, /archive→archive, /restore→restore, /purge→purge, /bulk-delete→delete, /assign-topic→assign, /comments→comment, /stage→transition, DELETE→delete, else edit).
4. **Creator scope** (`modules/record/services/creator_scope.py`) — for record resources, permission rows with `scope='creator'` restrict list/detail/mutations to rows the user created; unrestricted roles bypass.
5. **Service → repository → DB**; optimistic concurrency via `version` + `If-Match` (`core/concurrency.py`).
6. **Audit** — significant mutations append to `audit_log` (action_code, table_name, row_id, ip, status_code); notifications go through `outbox`.

## Response envelope

All endpoints return `DataEnvelope` (`core/http_schemas.py`): `{"data": ..., "meta": {page, limit, total, ...}}`. Errors: `core/errors.py` maps domain exceptions to HTTP (400/401/403/404/409/422/429/500) without stack traces.

## Modules

### people_access
- Auth API (`api/auth.py`): `bootstrap`, `register`, `login`, `me`, `refresh`, `logout`, `forgot-password` (+ verify/resend/reset), `change-password`, `profile/avatar` (PUT/DELETE).
- JWT HS256; access token minutes (default 480), refresh 7 days; HttpOnly cookies; bearer mode opt-in for non-browser clients.
- Password resets use HMAC digest codes (`password_reset_secret`), delivered via email/Telegram integrations.
- `users`, `users/roles` CRUD + counts/options/archive/restore/purge/bulk-delete/comments/activity/attachments; `users/permission-catalog` returns structured catalog rows (code, prefix, actions, scope).
- `permission` table rows carry `code`, `is_enable`, `scope` ('all'|'creator').
- Menu seed (`services/people.py: seed_menus`) populates `menu` table from the permission catalog.
- Officer ↔ user linkage (`auth_id` on officer, `officer_id` on users).

### record
- `api/dynamic_records.py` — the dynamic engine: `records/{type_code}` full CRUD + `counts`, `options`, `schema`, `activity`, `comments`, `neighbors`, `attachments` (PUT link / POST upload / DELETE detach), `archive`, `restore`, `purge`, `bulk-delete`, `stage` (transition), `reorder`, `assign-topic`, `records/_meta/surfaces`, `records/logs`.
- `api/configuration.py` — `configuration/record-types` + `configuration/record-attributes` CRUD, duplicate, bulk-delete, schema-by-id/code, per-type permissions (`record_type_permission`).
- `services/router_factory.py` builds per-type routers; `services/record_collections.py` implements list/create/update on Record rows; `services/support_collections.py` handles Entity-table resources (logs etc.).
- `services/meeting.py` — `assign_topic`, `reorder_meetings` (persist `topicId`/`topicTitle`/`sortOrder` into record payload), `link_drive_attachment`.
- `services/meeting_schedules.py` + `jobs/scheduler/meeting_reminders.py` — due-meeting reminders via Telegram/email through outbox.
- `services/creator_scope.py` — creator-only enforcement (see RBAC.md).
- `domain/map.py` — slug↔type-code map, `TYPE_UI_DEFAULTS` (auto-seed), `DOCUMENT_WORKFLOW_STAGES` (10 stages), `MEETING_WORKFLOW_STAGES` (4 stages), numbering prefixes, lifecycle mapping.

### organization
- `organizations/{org_type}` dynamic router for `department` | `company` (org rows), plus `_meta/types`.
- `purpose`, `sector` dedicated routers (sector has parent hierarchy).
- Organization model: `parent_id` hierarchy (cycle-safe), `sector_id`, `organization_purpose_id`, `tax_id`, contacts, `child_ids`, `organization_type`.
- Officers: `officers` CRUD; officer has `organization_id`, `role_id`, `auth_id` (nullable user link), identifiers table.

### storage_integration
- `portal/file-uploads` (Entity-backed) CRUD + archive/restore/purge/comments/attachments.
- `files/{file_id}` download (authorized, streams stored object).
- `records/{type}/{id}/attachments/upload` lives in `application/attachment_router.py` (composition layer): multipart upload → storage write → File metadata row → RecordAttachment link (single transaction boundary, permission-checked).
- Drive sync (`api/portal.py` + `services/drive_sync.py`): `drive-files` list, `sources` create, `sources/{id}/sync` (creates queued job Entity), `jobs/{job_id}` status; worker executes `run_sync_job` (queued → running → completed/failed, stores `files` rows with `source_table='drive-files'`).
- Providers (`api/settings_storage.py`): `settings/storage` CRUD + `test-connection`, `set-active`, `set-default`; credentials encrypted (`settings_encryption_key`).

### admin_config
- `settings/app-info` (GET/PUT/reset), `settings/app-config` (GET/PATCH) with email/telegram `test-connection` / `send-test` endpoints.
- `Setting` table: key_group, key, data_type, public_access, visible, ordering, key_value. `settings` table: simple key/value app-info store.

### reporting_support
- `dashboard/summary` — per-identity Redis cache (`dashboard_cache_key(user)` includes user id + permission fingerprint; permission-filtered KPIs, workByStage, recordsOverTime, meeting events).
- `search` — keyword-only (SQL ILIKE across record/organization/people/storage readers); response honestly reports `"mode": "keyword", "semanticAvailable": false`.
- `search/ask` — **honest placeholder**: `available: false`, no generated answer, returns real keyword citations.
- `mentions` — officer/department/company lookups for @mention fields.
- `exports` (`application/export_router.py` too): `POST /exports` creates job → worker `generate_export` builds CSV from selected fields/filters → `expiresAt` 24h; `GET /exports/{id}` status/download; `DELETE /exports/{id}`; scheduler `cleanup_expired_exports`.

## Concurrency & integrity

- `version` column + `If-Match` header on all mutable entities; mismatch → 409.
- Soft-delete lifecycle: `status` 1=active, 2=archived, 0=deleted (`LIFECYCLE_TO_STATUS`); `purge` is a hard delete gated by `deletable` flag and permissions.
- Rate limiting (`core/rate_limit.py`) on auth endpoints; secrets redacted in logs (`core/redaction.py`).

## Configuration (`core/config.py`, pydantic-settings)

Key groups: database/redis/rabbitmq URLs; session cookie names/secure/samesite, CSRF; JWT secrets + TTLs; password reset secret + URL; settings encryption key; SMTP; Telegram bots; Google Drive token/folder; `max_upload_size_mb` (25); S3/MinIO; worker/scheduler tuning. Secrets come from env files — never committed.
