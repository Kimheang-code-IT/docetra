# Dynamic record collections

Canonical contract for Docetra’s unified record surface. Prefer this document over older static path lists when they conflict.

## Principle

Operational items (documents, meetings, topics, and future types) are **records** differentiated by record type. Persistence joins **`record.record_type_id` → `record_type.id`**. `record_type.code` is informational and is **not unique**: HTTP `{typeCode}` is resolved inside the caller's permitted types (owner grant first, then oldest). There is **no separate meeting HTTP family** and **no `document_type` table**. Admins define attributes, assign them to types, and set type metadata (`uiSurface`, slug, icon). The creator organization owns a type and can share it with other organizations via `record_type_permission`. The API and UI must not require a new hardcoded collection or Vue page per type.

## API path shape

Use **only**:

```text
/api/v2/records/{typeCode}
/api/v2/records/{typeCode}/{id}
/api/v2/records/{typeCode}/schema
/api/v2/records/_meta/surfaces
/api/v2/records/logs
```

Do **not** mount `/api/v2/meetings/…` for CRUD or board ops. Do **not** mount bare `/api/v2/{typeCode}/…`.

`typeCode` must match `^[a-z][a-z0-9_]{1,63}$`. Resolve it to a `record_type.id` the caller can access; reject unknown, inactive, or unshared types with `404`.

Reserved path segments under `/records/` (not type codes): `_meta`, `logs`.

### Standard collection surface (every active type)

- `GET/POST` collection; `GET/PATCH/DELETE` item
- `POST …/archive`, `…/restore`, `…/bulk-delete`
- `DELETE …/purge`
- `PATCH …/stage`
- `GET …/counts`, `…/options`
- `GET/POST …/comments`, `GET …/activity`, `…/attachments`, `…/neighbors`, `…/favorite`
- `GET …/schema` — resolved create/detail schema
- `GET /records/_meta/surfaces` — types grouped by `uiSurface` for FE menus
- `GET /records/logs` — activity for **document-surface** types only

### Meeting board helpers (same record API)

Board-only ops live under the meeting type code (rows remain unified `record` rows):

```text
POST /api/v2/records/meeting_history/reorder
POST /api/v2/records/meeting_history/{id}/assign-topic
POST /api/v2/records/meeting_history/{id}/attachments/link
```

Permissions use `records.meeting_history.assign|edit` (not `meetings.history.*`).

There are **no** hyphenated HTTP aliases (`/records/incoming-documents`, `/records/documents`, …). UI may still use slug routes (`/records/incoming-documents` pages); the API always uses `typeCode` (`incoming_document`, `document`, …).

## Record type metadata (`record_type.payload`)

```json
{
  "uiSurface": "meeting",
  "slug": "history",
  "icon": "i-lucide-calendar",
  "menuOrder": 10,
  "isCreatable": true,
  "supportsStages": true,
  "supportsTopicContainer": false
}
```

| `uiSurface` | UI shell (frontend only) |
| --- | --- |
| `meeting` | Meeting menu; `/meetings/{slug}` |
| `document` | Record menu; `/records/{slug}`; included in document logs |
| `system` | Hidden from create menus |

## Permissions

Generate capabilities from type codes: `records.{typeCode}.{action}` for the standard workflow action set. New types must not require hand-edited permission rows.

## Frontend shells

- Boot: `GET /records/_meta/surfaces`.
- Menus: group active types by `uiSurface` only (no hardcoded entity-key menu).
- Routes: `/meetings/[typeCode]`, `/records/[typeCode]` (+ `new`, `[id]`) — dynamic only.
- Adapter: `createRecordAdapter(typeCode)` → `/api/v2/records/${typeCode}`.
- Topic board UI when `supportsTopicContainer` / `meeting_topic`; still uses record APIs.

## Non-record (stay static)

Users/roles, settings, portal Drive, auth, search, exports, mentions, files.

Organizations: [`08-dynamic-organization-collections.md`](./08-dynamic-organization-collections.md).

## Related

- [`modules/record.md`](../specification/modules/record.md)
- [`00-integration-contract.md`](./00-integration-contract.md)
- [`../frontend/00C-dynamic-record-fields.md`](../frontend/00C-dynamic-record-fields.md)
- [`../idea/03-draft-db-design.md`](../idea/03-draft-db-design.md)
