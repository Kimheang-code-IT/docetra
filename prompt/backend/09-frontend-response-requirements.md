# Frontend Response Requirements (Backend Master Contract)

This is the **single backend reference** for what every `/api/v2` endpoint must accept and return so the shipped Nuxt app works without page changes.

**Authority order**

1. `frontend/app/utils/constants/api-endpoints.ts` — exact paths
2. `frontend/app/types/docetra/*` and `frontend/app/types/auth-user.ts` — response field names and shapes
3. `frontend/app/adapters/*` — HTTP methods, query params, and mutation bodies
4. This document — consolidated rules and per-area requirements
5. `prompt/backend/modules/*.md` — field-level business rules
6. `prompt/specification/06-api-contracts.md` — global REST conventions

When a path or JSON key disagrees with the frontend adapter, **fix the backend or update the adapter together**. Do not invent shorter URLs or snake_case JSON keys.

---

## 1. Global response rules

### 1.1 Envelopes

| Operation | HTTP | Body |
| --- | --- | --- |
| Detail / mutation success | 200, 201, 202 | `{ "data": { ... } }` |
| List success | 200 | `{ "data": [ ... ], "meta": { "page", "limit", "total", "totalPages" } }` |
| Client error | 4xx | `{ "message": "...", "error": { "code", "message", "fields", "requestId" } }` |

Optional list meta: `cursor`, `nextCursor` (future). Frontend today uses page/limit only.

### 1.2 JSON naming

- API JSON keys are **camelCase** (`recordTime`, `createdAt`, `pageAccess`).
- PostgreSQL columns stay snake_case (`record_time`, `created_at`).
- Never return password hashes, JWTs, SMTP passwords, bot tokens, storage secrets, or encryption keys in GET responses. Mask with `••••••` where a field must exist for edit forms.

### 1.3 Timestamps

- Store UTC in PostgreSQL (`timestamptz`).
- Return ISO 8601 with `Z` suffix: `2026-08-18T01:30:00.000Z`.
- Accept offset forms on input; normalize to UTC on output.
- Date-only fields: `YYYY-MM-DD`.
- Datetime-local list filters (`2026-08-18T08:30` without offset) are interpreted in App Config IANA timezone. Full rules: [`07-datetime-and-list-query.md`](./07-datetime-and-list-query.md).

### 1.4 Lifecycle status (business records)

Cards, lists, and master data use exactly:

| Value | UI label | Meaning |
| --- | --- | --- |
| `active` | Active | Normal use |
| `archived` | Archived | Hidden from default lists |
| `deleted` | Deleted | Soft-deleted tombstone |

Workflow position is separate field `stage` (string). There is no business lifecycle value `completed`.

Separate domain enums (do not mix into card Status):

- User account: `active`, `disabled`, `locked`, `deleted`
- Jobs/uploads: `queued`, `processing`, `completed`, `failed`, `ready`
- Record type publication: `draft`, `published`

### 1.5 Identity fields on every entity record

Every collection item returned by `createEntityAdapter` must include at minimum:

```json
{
  "id": "uuid",
  "status": "active",
  "createdAt": "2026-08-18T08:30:00.000Z",
  "updatedAt": "2026-08-18T08:30:00.000Z",
  "version": 1
}
```

Optional when applicable: `stage`, `archivedAt`, `deletedAt`, `recordTime`, `title`, `name`, `code`.

PATCH/PUT bodies may include `version` for optimistic concurrency. Return `409` when stale.

### 1.6 List query parameters (all entity collections)

| Param | Type | Contract |
| --- | --- | --- |
| `page` | int | 1-based, default 1 |
| `limit` | int | default 20; cap 100; `all`/`-1` → cap 100 |
| `q` / `search` | string | Case-insensitive payload search |
| `sort` | string | `-updatedAt` = desc; supported: `createdAt`, `updatedAt`, `recordTime`, `meetingDate` |
| `status` | string | Comma-separated; default lists exclude `archived` and `deleted` |
| `stage` | string | Comma-separated stage ids; `__empty__` = unassigned |
| `startDate` / `endDate` | string | Inclusive range; see datetime doc |
| `view` | string | `table` \| `kanban` \| `hierarchy` \| `timeline` — hint only |
| Extra keys | string | Equality filter on payload field when not reserved |

`GET {base}/options` additionally accepts: `q`, `limit`, `status`, `valueField`, `hierarchy=true`, `excludeId`.

`GET {base}/counts` accepts `groupBy` (default `stage`).

---

## 2. Authentication responses

Frontend source: `frontend/app/adapters/auth.ts`, `frontend/app/types/auth-user.ts`.

| Method | Path | Request | Response `data` |
| --- | --- | --- | --- |
| POST | `/auth/login` | `{ email, password }` | `{ user: AuthUser }` — sets cookies; **no token in JSON** |
| GET | `/auth/me` | — | `AuthUser` |
| POST | `/auth/refresh` | — | `{ user: AuthUser }` — rotates session |
| POST | `/auth/logout` | — | `{ loggedOut: true }` |
| POST | `/auth/forgot-password` | `{ email }` | `{ sent: true }` (+ `debugCode` in development only) |
| POST | `/auth/forgot-password/resend` | `{ email }` | `{ sent: true }` |
| POST | `/auth/forgot-password/verify` | `{ email, code }` | `{ verified: true }` |
| POST | `/auth/forgot-password/reset` | `{ email, code, password, passwordConfirmation }` | `{ reset: true }` |
| POST | `/auth/change-password` | `{ currentPassword, password, passwordConfirmation }` | `{ changed: true }` |
| PUT | `/auth/profile/avatar` | `{ avatar }` data URL PNG/JPEG/WebP/GIF ≤ 2 MB | `{ avatar }` |
| DELETE | `/auth/profile/avatar` | — | `{ removed: true }` |

### AuthUser shape

```ts
{
  id: string            // UUID string in production
  name: string
  email: string
  role?: string
  avatar?: string
  permissions?: string[]   // flat keys, e.g. records.incoming_documents.view
  pageAccess?: string[]    // ["ALL_PAGES"] for SuperAdmin/Admin; else omit or []
}
```

Cookies (HttpOnly unless noted):

- `docetra_session` — access JWT
- `docetra_refresh` — refresh JWT
- `XSRF-TOKEN` — readable CSRF cookie; mutations send `X-CSRF-Token` header

401 → session dialog. 403 → permission dialog (stay on page).

---

## 3. Shared entity adapter surface

Frontend source: `frontend/app/adapters/createEntityAdapter.ts`.

Every collection below implements this HTTP surface relative to its `{base}`:

| Method | Path | Adapter method | Response |
| --- | --- | --- | --- |
| GET | `{base}` | `list` | `{ data: T[], meta }` |
| GET | `{base}/{id}` | `get` | `{ data: T }` |
| POST | `{base}` | `create` | `{ data: T }` — 201 |
| PATCH | `{base}/{id}` | `update` | `{ data: T }` |
| POST | `{base}/{id}/archive` | `archive` | `{ data: T }` |
| POST | `{base}/{id}/restore` | `restore` | `{ data: T }` |
| DELETE | `{base}/{id}` | `delete` | `{ data: { id } }` — soft delete |
| POST | `{base}/bulk-delete` | `deleteMany` | `{ data: { ids: string[] } }` |
| DELETE | `{base}/{id}/purge` | `purge` | `{ data: { id } }` — admin only |
| PATCH | `{base}/{id}/stage` | `transitionStage` | `{ data: T }` — body `{ stage }` |
| GET | `{base}/counts` | `getGroupCounts` | `{ data: GroupCountSummary }` |
| GET | `{base}/options` | reference options | `{ data: OptionItem[] }` |
| GET | `{base}/{id}/comments` | `listComments` | `{ data: EntityComment[], meta? }` |
| POST | `{base}/{id}/comments` | `addComment` | `{ data: EntityComment }` |
| PATCH | `{base}/{id}/comments/{cid}` | `updateComment` | `{ data: EntityComment }` |
| DELETE | `{base}/{id}/comments/{cid}` | `deleteComment` | `{ data: { id } }` |
| GET | `{base}/{id}/activity` | `listActivity` | `{ data: ActivityEvent[], meta? }` |
| GET | `{base}/{id}/attachments` | `listAttachments` | `{ data: AttachmentMeta[] }` |
| PUT/POST | `{base}/{id}/attachments` | `replaceAttachments` | `{ data: AttachmentMeta[] }` |
| GET | `{base}/{id}/neighbors` | `getNeighbors` | `{ data: { previousId, nextId } }` |
| GET | `{base}/{id}/favorite` | `getFavorite` | `{ data: { isFavorite } }` |
| PUT | `{base}/{id}/favorite` | `setFavorite` | `{ data: { isFavorite } }` — body `{ isFavorite }` |

### Shared sub-object shapes

**EntityComment**

```json
{
  "id": "uuid",
  "entityType": "records/incoming-documents",
  "entityId": "uuid",
  "body": "text",
  "author": { "id", "name", "email", "avatarUrl?" },
  "createdAt": "ISO",
  "editedAt": "ISO?"
}
```

**ActivityEvent**

```json
{
  "id": "uuid",
  "entityType": "string",
  "entityId": "uuid",
  "action": "created|updated|archived|...",
  "summary": "human readable",
  "actor": { "id", "name", "email", "avatarUrl?" },
  "occurredAt": "ISO",
  "metadata": {}
}
```

**AttachmentMeta**

```json
{
  "id": "uuid",
  "name": "file.pdf",
  "mimeType": "application/pdf",
  "sizeBytes": 12345,
  "url": "/api/v2/files/{id}",
  "uploadedAt": "ISO",
  "storageSource": "local|google_drive"
}
```

**GroupCountSummary**

```json
{ "total": 10, "unassigned": 2, "groups": { "review": 5, "approved": 3 } }
```

**Option item** (`GET {base}/options`)

```json
{
  "id": "uuid",
  "label": "Display name",
  "value": "uuid or field value",
  "parentId": "uuid?",
  "meta": { "id", "name", "code", "depth?" }
}
```

Read-only collections (no POST create): `records/logs`, `portal/logs`, `system/logs`.

---

## 4. Collection bases and entity payloads

Router map: [`06-backend-file-structure.md` §5.3](./06-backend-file-structure.md).

| Adapter key | Base path | Primary TypeScript type | Module doc |
| --- | --- | --- | --- |
| `meetingTopics` | `/meetings/topics` | `MeetingTopic` | [`modules/meeting-topic-board.md`](./modules/meeting-topic-board.md) |
| `meetingHistory` | `/meetings/history` | `MeetingHistory` | [`modules/meeting-topic-board.md`](./modules/meeting-topic-board.md) |
| `incomingDocuments` | `/records/incoming-documents` | `RecordDocument` | [`modules/record-workflow-boards.md`](./modules/record-workflow-boards.md) |
| `outgoingDocuments` | `/records/outgoing-documents` | `RecordDocument` | same |
| `documents` | `/records/documents` | `RecordDocument` | same |
| `masterListRequests` | `/records/master-list-requests` | `RecordDocument` | same |
| `recordLogs` | `/records/logs` | `RecordLog` | same |
| `departments` | `/organizations/departments` | `Department` | [`modules/organization-master-data.md`](./modules/organization-master-data.md) |
| `companies` | `/organizations/companies` | `Company` | same |
| `purposes` | `/purpose` | `Purpose` | same |
| `sectors` | `/sector` | `Sector` | same |
| `officers` | `/officers` | `Officer` | same |
| `roles` | `/users/roles` | `Role` | [`modules/user-management.md`](./modules/user-management.md) |
| `users` | `/users` | `UserAccount` | same |
| `recordTypes` | `/configuration/record-types` | `RecordType` | [`modules/configuration-record-metadata.md`](./modules/configuration-record-metadata.md) |
| `recordAttributes` | `/configuration/record-attributes` | `RecordAttribute` | same |
| `fileUploads` | `/portal/file-uploads` | `FileUpload` | [`modules/portal-operations.md`](./modules/portal-operations.md) |
| `googleDriveSync` | `/portal/google-drive-sync` | `GoogleDriveSync` | same |
| `portalLogs` | `/portal/logs` | `PortalLog` | same |
| `systemLogs` | `/system/logs` | `SystemLog` | same |

### RecordDocument required fields by kind

| Field | Incoming | Outgoing | Document | Master list |
| --- | --- | --- | --- | --- |
| `title` | ✓ | ✓ | ✓ | ✓ |
| `status` | ✓ | ✓ | ✓ | ✓ |
| `referenceNumber` / letter no. | ✓ | ✓ | ✓ | — |
| `documentType` (company id) | ✓ | ✓ | ✓ | — |
| `receivedDate` | ✓ | — | — | — |
| `sentDate` | — | ✓ | — | — |
| `documentDate` | — | — | ✓ | — |
| `officeInCharge` | ✓ | ✓ | ✓ | — |
| `involvedOfficers` | ✓ | ✓ | ✓ | — |
| `externalUnits` | ✓ | ✓ | ✓ | — |
| `recordTime` | ✓ | ✓ | ✓ | ✓ |
| `recordTag` / `tags` | optional | optional | optional | ✓ |
| `stage` | ✓ | ✓ | ✓ | ✓ |
| `details` | optional dynamic attrs | optional | optional | — |

Do **not** require on create for incoming/outgoing/document: `recordFlowCode`, free-text `recordContent`, or `recordTypeId` as the document-type select.

### MeetingHistory required fields

`title`, `meetingDate`, `letterNumber`, `letterDate`, `status`, `stage?`, `topicId?`, `sortOrder?`, `notes`/`recordContent`, `recordTime`, `durationMinutes?`, `meetingMode?`, `meetingUrl?`, `location?`, `recurrence?`, `attachments[]`.

Optional computed timing fields: `imminent`, `minutesUntilStart`, `inProgress` (see `MeetingBoardTiming`).

---

## 5. Special endpoints (non-entity adapter)

### 5.1 Dashboard — `GET /dashboard/summary`

Frontend type: `DashboardSummary` in `frontend/app/types/docetra/entities.ts`.

**Required response shape:**

```json
{
  "data": {
    "kpis": [
      {
        "id": "incoming-documents",
        "labelKey": "docetra.pages.incomingDocuments",
        "value": 42,
        "trend": 3,
        "href": "/records/incoming-documents",
        "updatedAt": "2026-08-18T08:30:00.000Z"
      }
    ],
    "workByStage": [
      { "stage": "review", "count": 12 }
    ],
    "recordsOverTime": [
      { "date": "2026-08-01", "count": 5 }
    ],
    "events": [
      {
        "id": "uuid",
        "title": "Weekly sync",
        "start": "2026-08-18T09:00:00.000Z",
        "end": "2026-08-18T10:00:00.000Z",
        "allDay": false,
        "color": "primary",
        "type": "meeting",
        "href": "/meetings/history/uuid",
        "location": "Room A"
      }
    ]
  }
}
```

Permission: `dashboard.view`. Short-cache allowed (≈30s). Must respect user capabilities when counting.

> **Alignment note:** current backend returns a flat count object (`totalRecords`, `recentActivity`, …). Update backend to match `DashboardSummary` before dashboard cutover.

### 5.2 Search — `GET /search`, `POST /search/ask`

Frontend types: `SearchHit`, `AiSearchAnswer` in `frontend/app/types/docetra/search.ts`.

**GET `/search?q=&mode=keyword|semantic&limit=12`**

```json
{
  "data": [
    {
      "id": "uuid",
      "entityType": "incomingDocument",
      "entityId": "uuid",
      "title": "Letter 123",
      "text": "full searchable text",
      "snippet": "short preview",
      "url": "/records/incoming-documents/uuid",
      "permission": "records.incoming_documents.view",
      "updatedAt": "ISO",
      "score": 1,
      "sourceLabel": "Incoming document"
    }
  ]
}
```

Filter results by user permissions before returning. Empty `q` → `{ "data": [] }`.

**POST `/search/ask`**

Request: `{ "q": "string", "hitIds": ["uuid", ...] }`

Response:

```json
{
  "data": {
    "answer": "Summary text with citations",
    "citations": [ /* SearchHit[] */ ]
  }
}
```

### 5.3 Exports — `POST /exports`, `GET /exports/{id}`

Frontend types: `ExportJob`, `CreateExportJobInput` in `frontend/app/types/docetra/export.ts`.

**POST `/exports`** — body:

```json
{
  "resource": "incomingDocuments",
  "format": "csv",
  "scope": "all_matching|current_page|selected",
  "fieldCodes": ["title", "status", "recordTime"],
  "startDate": "2026-08-01",
  "endDate": "2026-08-31",
  "selectedIds": ["uuid"],
  "query": { "stage": "review" }
}
```

Response **202**:

```json
{
  "data": {
    "id": "uuid",
    "status": "queued",
    "resource": "incomingDocuments",
    "createdAt": "ISO"
  }
}
```

**GET `/exports/{id}`** — poll until terminal:

```json
{
  "data": {
    "id": "uuid",
    "status": "queued|processing|completed|failed",
    "resource": "incomingDocuments",
    "createdAt": "ISO",
    "downloadUrl": "/api/v2/files/{jobId}",
    "expiresAt": "ISO",
    "error": "message when failed"
  }
}
```

Resource key mapping (frontend → backend collection):

| Frontend `resource` | Collection |
| --- | --- |
| `incomingDocuments` | `incoming-documents` |
| `outgoingDocuments` | `outgoing-documents` |
| `documents` | `documents` |
| `masterListRequests` | `master-list-requests` |
| `meetingTopics` | `meeting-topics` |
| `meetingHistory` | `meeting-history` |
| … | see `RESOURCE_MAP` in backend exports module |

### 5.4 Mentions — `GET /mentions`

Query: `q`, `type=officer|department|company`, `limit` (default 20, max 50).

```json
{
  "data": [
    { "id": "uuid", "label": "Officer Name", "type": "officer" }
  ]
}
```

Permission-filter before return. Used by `AppMentionMultiInput`.

### 5.5 Meeting board extras

Frontend: `frontend/app/adapters/meeting-board.ts`.

| Method | Path | Body | Response `data` |
| --- | --- | --- | --- |
| POST | `/meetings/reorder` | `{ topicId, orderedMeetingIds[] }` | `{ topicId, orderedMeetingIds }` |
| POST | `/meetings/history/{id}/assign-topic` | `{ topicId, sortOrder?, topicTitle? }` | `MeetingHistory` |
| POST | `/meetings/history/{id}/attachments/link` | `{ source:"google_drive", driveFileId, displayName?, ... }` | `AttachmentMeta` |
| GET | `/portal/drive-files` | query `search`, `page`, `limit` | `{ data: DriveFileCatalogItem[], meta }` |

### 5.6 Configuration schema — record type

| Method | Path | Response |
| --- | --- | --- |
| GET | `/configuration/record-types/by-code/{code}/schema` | `{ data: { recordType, tabs, fields, workflowStages, version } }` (`recordType` includes `id`, optional `ownerOrganizationId`, `organizationIds`) |
| GET | `/configuration/record-types/{id}/schema` | same |
| GET | `/configuration/record-types/{id}/permissions` | `{ data: [{ id, organizationId, recordTypeId, permissionKind }] }` |
| POST | `/configuration/record-types/{id}/permissions` | body `{ organizationId }` → permission row |
| DELETE | `/configuration/record-types/{id}/permissions/{organizationId}` | `{ data: { organizationId } }` |

Used by dynamic document forms (`useRecordTypeDrivenTabs`).

### 5.7 Permission catalog — `GET /users/permission-catalog`

```json
{
  "data": [
    {
      "documentType": "incoming_document",
      "labelKey": "docetra.permissions.types.incomingDocument",
      "permissionPrefix": "records.incoming_documents",
      "actions": ["view", "create", "edit", "archive", "restore", "delete", "purge", "export", "comment", "transition"]
    }
  ]
}
```

Must match `frontend/app/utils/role/permissions.ts`. Published record types are appended dynamically.

### 5.8 Settings singletons

Frontend types: `frontend/app/types/docetra/settings.ts`.

| Path | Type | Notes |
| --- | --- | --- |
| GET/PATCH `/settings/app-info` | `AppInfo` | Branding, footer, support contacts |
| POST `/settings/app-info/reset` | `AppInfo` | Restore defaults |
| GET/PATCH `/settings/app-config` | `AppConfig` | General, email, telegram, notifications, security, system, display |
| POST `/settings/app-config/email/test-connection` | `{ status, message, testedAt }` | Side effect only |
| POST `/settings/app-config/telegram/test-connection` | same | Side effect only |
| GET/POST `/settings/storage` | `StorageProvider[]` | List/create |
| GET/PATCH/DELETE `/settings/storage/{id}` | `StorageProvider` | CRUD |
| POST `/settings/storage/{id}/test-connection` | connection result | |
| POST `/settings/storage/{id}/set-default` | `StorageProvider` | |
| POST `/settings/storage/{id}/set-active` | `StorageProvider` | body `{ active: boolean }` |

Secrets (`password`, `botToken`, `accessKey`, …) are masked on GET, encrypted at rest, accepted on PATCH only when changed.

Details: [`modules/settings-application.md`](./modules/settings-application.md).

### 5.9 File download — `GET /files/{fileId}`

Streams binary content with correct `Content-Type` and `Content-Disposition`. Requires auth; enforces upload permission for non-admin users.

Multipart create on entity collections (`POST {base}` with `multipart/form-data`) returns the created record with `objectKey`, `url`, `mimeType`, `sizeBytes`, `fileName`.

---

## 6. Permission keys the frontend enforces

Flat pattern: `{permissionPrefix}.{action}`.

| Prefix | Actions |
| --- | --- |
| `dashboard` | view |
| `records.incoming_documents` | view, create, edit, archive, restore, delete, purge, export, comment, transition |
| `records.outgoing_documents` | same |
| `records.documents` | same |
| `records.master_list_requests` | same |
| `records.logs` | view, export |
| `meetings.topics` | workflow set |
| `meetings.history` | workflow set + assign |
| `organizations.*` | master-data set |
| `users.users`, `users.roles` | view, create, edit, archive, restore, delete, purge, comment, configure |
| `configuration.record_types`, `configuration.record_attributes` | config set |
| `portal.file_upload` | view, create, delete, share, export |
| `portal.google_drive_sync` | config set |
| `portal.logs`, `system.logs` | view, export |
| `settings.app_info`, `settings.app_config`, `settings.storage` | view, edit, configure |

`/auth/me` must return the expanded flat list in `permissions`. SuperAdmin/Admin also get `pageAccess: ["ALL_PAGES"]`.

Creator-scoped roles: when `onlyIfCreator` is set on a permission row, non-admin users may only mutate records they created.

---

## 7. Frontend type → backend file map

| Frontend type file | Backend responsibility |
| --- | --- |
| `types/auth-user.ts` | `api/v2/auth.py` response shaping |
| `types/docetra/common.ts` | Shared envelopes, comments, activity, attachments, list meta |
| `types/docetra/entities.ts` | Entity payload fields per collection |
| `types/docetra/meeting-api.ts` | Meeting board special routes |
| `types/docetra/configuration.ts` | Record type/attribute/schema responses |
| `types/docetra/settings.ts` | App info/config/storage singletons |
| `types/docetra/search.ts` | Search + ask responses |
| `types/docetra/export.ts` | Export job lifecycle |
| `adapters/createEntityAdapter.ts` | Generic CRUD router factory |
| `adapters/meeting-board.ts` | Meeting-specific routes |
| `adapters/auth.ts` | Auth routes |
| `adapters/search.ts` | Search routes |
| `adapters/exports.ts` | Export routes |
| `utils/constants/api-endpoints.ts` | Canonical path list for contract tests |

Database layer (separate from API JSON): `backend/app/db/` + `backend/app/models/`. See [`06-backend-file-structure.md` §7](./06-backend-file-structure.md).

---

## 8. Backend alignment checklist

Use this before declaring an area "frontend-ready".

### Global

- [ ] All paths in `api-endpoints.ts` are routed (contract test)
- [ ] JSON keys are camelCase
- [ ] Envelopes match §1.1
- [ ] CSRF on mutations; cookies on auth
- [ ] 401/403 semantics match frontend dialogs
- [ ] Default lists hide archived/deleted unless `status` filter passed
- [ ] `version` optimistic locking returns 409

### Per area

| Area | Key response checks |
| --- | --- |
| Auth | `AuthUser` shape; no JWT in JSON; permissions flat |
| Entity collections | Full adapter surface §3 |
| Dashboard | `DashboardSummary` shape §5.1 |
| Search | `SearchHit[]` permission-filtered |
| Exports | 202 + poll `ExportJob` |
| Meetings | reorder, assign-topic, drive link |
| Settings | masked secrets; `AppConfig` localization fields |
| Configuration | `/schema` for dynamic forms |
| Portal uploads | multipart create + `/files/{id}` download |
| Logs | read-only; `occurredAt` indexed |

### Known gaps to close in `backend/`

1. ~~**Dashboard** — return `kpis`, `workByStage`, `recordsOverTime`, `events` (not flat counts).~~ **Done** — see `modules/reporting_support/dashboard.py`.
2. ~~**Search** — map `entityType` to frontend enum values (`incomingDocument`, not `incoming-documents`).~~ **Done** — see `modules/reporting_support/search.py` and `core/frontend_contract.py`.
3. ~~**Assignee arrays** — return `{ id, label, type }[]` on assignee fields when UI expects mention tags.~~ **Done (basic)** — `normalize_assignment_refs()` in `stamp()`; optional DB label resolution can follow later.
4. **Pydantic schemas** — optional but recommended: reintroduce `schemas/` mirroring frontend types for OpenAPI accuracy.

---

## 9. Verification commands

```powershell
cd backend
pip install ".[test]"
pytest tests/test_contract.py -q          # every ApiEndpoints path exists
pytest -q                               # full suite

# With Docker stack running:
docker compose --env-file backend.env -f compose.backend.yml run --rm api python scripts/smoke.py
```

Frontend side:

```bash
cd frontend
pnpm typecheck
NUXT_PUBLIC_USE_MOCK_DATA=false NUXT_PUBLIC_API_BASE=http://localhost:8000 pnpm dev
```

Walk through: login → dashboard → one record board → one document detail → settings save → export → search.

---

## 10. Related documents

| Doc | Use when |
| --- | --- |
| [`00-integration-contract.md`](./00-integration-contract.md) | Session, CSRF, lifecycle, assignment rules |
| [`06-backend-file-structure.md`](./06-backend-file-structure.md) | File tree and router map |
| [`07-datetime-and-list-query.md`](./07-datetime-and-list-query.md) | Dates, filters, `record_time` |
| [`08-implementation-sequence.md`](./08-implementation-sequence.md) | Sprint build order |
| [`modules/*.md`](./modules/) | Field-level rules per product area |
| [`../specification/06-api-contracts.md`](../specification/06-api-contracts.md) | Engineering REST conventions |
| [`../../frontend/docs/api-integration-guide.md`](../../frontend/docs/api-integration-guide.md) | Frontend-side integration steps |
