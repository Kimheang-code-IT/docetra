# Docetra — API

Base path `/api/v2`. **355 registered operations** (verified from the running app). OpenAPI at `/api/v2/openapi.json`, docs at `/api/v2/docs`.

Response envelope (`DataEnvelope`): `{ "data": ..., "meta": { page, limit, total, pages? } }`.

Standard query contract for list endpoints: `q` (search), `page`, `limit`, `sort`, `view`, `status`, `stage`, `startDate`, `endDate`, `groupBy`. Standard list metadata: items in `data`, `total/page/limit` in `meta`. `counts` endpoints return grouped totals; `options` endpoints feed selects (`valueField=id`).

Mutations require `If-Match` (version) → 409 on conflict.

## Auth (`/auth`)

| Method + path | Purpose |
|---|---|
| GET `/auth/bootstrap` | Public system bootstrap info |
| POST `/auth/register` | Register (seeds first user/admin flows) |
| POST `/auth/login` | Email+password → HttpOnly session cookies (+bearer opt-in) |
| GET `/auth/me` | Current user + permissions (background session validation) |
| POST `/auth/refresh` | Rotate access+refresh from refresh cookie |
| POST `/auth/logout` | Clear both cookies |
| POST `/auth/forgot-password` `/resend` `/verify` `/reset` | Code-based reset (digest, TTL) |
| POST `/auth/change-password` | Authenticated change |
| PUT/DELETE `/auth/profile/avatar` | Avatar URL |

Errors: 401 invalid credentials/expired, 429 rate-limited, 422 validation.

## Record engine (`/records`)

Dynamic per type code (`meeting_topic`, `meeting_history`, `incoming_document`, `outgoing_document`, `document`, `master_list_request`, + admin-created):

| Operation | Endpoints |
|---|---|
| List | `GET /records/{type_code}` (`q,page,limit,sort,status,stage,startDate,endDate,topicId,excludeStage`) |
| Counts | `GET /records/{type_code}/counts` |
| Options | `GET /records/{type_code}/options` |
| Schema | `GET /records/{type_code}/schema` (fields, stages, features for the form renderer) |
| Detail | `GET /records/{type_code}/{id}` |
| Create | `POST /records/{type_code}` |
| Update | `PUT /records/{type_code}/{id}` (If-Match) |
| Stage transition | `PATCH /records/{type_code}/{id}/stage` (action `transition`) |
| Assign topic | `POST /records/meeting_history/{id}/assign-topic` (`topicId, topicTitle, sortOrder`; `topicId: null` = unassign) |
| Reorder | `POST /records/meeting_history/reorder` (`{topicId, orderedMeetingIds}`) |
| Attachments | `PUT .../attachments` (link metadata), `POST .../attachments/upload` (multipart bytes → File → RecordAttachment), `POST .../attachments/link` (Drive file link), `DELETE .../attachments/{file_id}` (detach, keeps File) |
| Comments | `GET/POST .../comments`, `PATCH/DELETE .../comments/{comment_id}` |
| Activity | `GET .../activity` |
| Neighbors | `GET .../neighbors` (prev/next for detail paging) |
| Lifecycle | `POST .../archive`, `POST .../restore`, `DELETE .../{id}` (soft delete), `DELETE .../purge`, `POST .../bulk-delete` |
| Surfaces | `GET /records/_meta/surfaces` (active types grouped by uiSurface → menus/routes) |
| Logs | `GET /records/logs` (cross-type audit view) |

## Configuration (`/configuration`)

- `record-types`: GET list/counts/options, GET `/{id}` + `/{id}/schema`, GET `/by-code/{code}/schema`, POST create, PUT/PATCH update, POST `duplicate`, `archive`, `restore`, `bulk-delete`, DELETE + `/purge`, GET/POST/DELETE `/{id}/permissions` (organization×kind), comments/activity/attachments/neighbors.
- `record-attributes`: same family (attribute catalog).
- ⚠ `GET/POST/PATCH/DELETE /configuration/enums...` — **not implemented** in the backend though frontend constants exist (`CONFIGURATION_ENUMS`). See GAP_ANALYSIS.

## Organizations

- `GET/POST /organizations/{org_type}` (`department`|`company`), full CRUD + archive/restore/purge/bulk-delete/comments/activity/attachments/neighbors/counts/options.
- `GET /organizations/_meta/types`.
- `/purpose`, `/sector`: same family; sector supports `parentId` (sub-sectors).
- `/officers`: CRUD + archive/restore/purge/bulk-delete/comments/attachments/counts/options.

## People access

- `/users`: CRUD + archive/restore/purge/bulk-delete/comments/attachments/counts/options.
- `/users/roles`: same family; role payload includes `permissionRows` (`code`, enabled, scope).
- `GET /users/permission-catalog` — structured catalog (prefix, actions, scope) — canonical contract for the role matrix.

## Portal

- `/portal/file-uploads`: list/create/detail/update + archive/restore/purge/bulk-delete/comments/activity/attachments/neighbors/counts/options.
- `/portal/google-drive-sync`: sources CRUD + `POST /portal/google-drive-sync/sources` (create source), `POST /portal/google-drive-sync/sources/{source_id}/sync` (start job), `GET /portal/google-drive-sync/jobs/{job_id}` (poll), plus CRUD/neighbors/etc.
- `GET /portal/drive-files` — synced Drive files.
- `/portal/logs`: read-only audit list (+ detail/comments/neighbors).

## Files

- `GET /files/{file_id}` — authorized download (streams object, filename + content type).

## Settings

- `GET/PUT /settings/app-info`, `POST /settings/app-info/reset`.
- `GET/PATCH /settings/app-config`; `POST .../email/test-connection`, `.../email/send-test`, `.../telegram/test-connection`, `.../telegram/send-test`.
- `/settings/storage`: GET list, POST create, GET/PUT/PATCH/DELETE `/{id}`, `POST /{id}/test-connection`, `/{id}/set-default`, `/{id}/set-active`.

## Reporting & cross-cutting

- `GET /dashboard/summary` — per-user Redis-cached KPIs (permission-filtered).
- `GET /search?q&mode&limit` — keyword-only; returns `meta.mode='keyword', semanticAvailable=false`.
- `POST /search/ask` — honest placeholder: `available:false` + real keyword citations.
- `GET /mentions?q&type` — officer/department/company mention lookups.
- `POST /exports` (job), `GET /exports/{id}`, `DELETE /exports/{id}`.
- `GET/POST/PATCH/DELETE /system/logs...` (read-oriented audit; delete/purge guarded).

## Health/ops (no auth)

`GET /health`, `GET /ready`, `GET /metrics`, `GET /docs`, `GET /openapi.json`.

## Error contract

| Status | Meaning | Frontend behavior |
|---|---|---|
| 400 | Bad request | Toast/inline |
| 401 | Unauthenticated | Silent refresh; logout only if refresh fails |
| 403 | Forbidden (permission) | Permission error, **no logout** |
| 404 | Not found | Not-found UI |
| 409 | Version conflict / duplicate | Conflict message + reload |
| 422 | Validation | Field-level form errors |
| 429 | Rate limited | Retry feedback |
| 5xx | Server failure | Generic safe message |
