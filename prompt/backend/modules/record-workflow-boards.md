# Record Module — Workflow Boards & Logs (Backend Logic)

> **UI scope:** Record nav — Incoming / Outgoing / Document / Master List Request (stage boards) + **Logs** (audit board).  
> **Record model:** All are `record` rows differentiated by `record_kind` / route slug, not separate domains.  
> **References:** `prompt/specification/modules/record.md`, `prompt/frontend/00-product-ui-design-map.md` (1+3 boards), `frontend/app/config/entities.ts` (`orgSelectDocumentTabs`, `masterListRequestTabs`), `useRecordStageBoard`, `useRecordLogBoard`.

---

## 1. Purpose

Record operational pages share one pattern:


| Route                           | UI                    | Backend role                               |
| ------------------------------- | --------------------- | ------------------------------------------ |
| `/records/incoming-documents`   | `AppRecordStageBoard` | Workflow stages + card grid; drag to stage |
| `/records/outgoing-documents`   | same                  | same                                       |
| `/records/documents`            | same                  | same                                       |
| `/records/master-list-requests` | same                  | same                                       |
| `/records/record-logs`          | `AppRecordLogBoard`   | Read-only log views + dynamic table        |
| `/*/new`, `/*/:id`              | `EntityDocumentView`  | Create / detail / edit (form schema below) |


**Stage boards (1+3):**

- **Left:** workflow stages (All + stage cards with counts); search stages; collapsible icon rail.
- **Right:** record **cards** in columns; date range + search; drag card onto stage to transition; row/card actions Detail / Logs / Delete.
- **Card fields:** App Config → Display → `incomingDocuments` | `outgoingDocuments` | `documents` | `masterListRequests` (`useCardFields`).

**Document pages (current UI contract):**

- Incoming / Outgoing / Document use a **shared org-select form** (no Record flow, no free-text content blob labeled Incoming/Outgoing/Document).
- Master List Request uses a **minimal** form (status, title, record time, tags only).
- Optional: Configuration **Record Type** attributes may still merge via `useRecordTypeDrivenTabs` when a type is linked — not required for the base form fields above.
- Standard document stack: comments, activity, attachments, meta rail.

**Record logs:**

- Left tabs filter **view** (All, Created, Updated, Stage, Shared, Incoming, Outgoing, Errors).
- Right table columns/filters change per tab; read-only; detail at `/records/record-logs/:id`.
- Pagination supports page sizes **10 / 20 / 50 / 100 / All** (`limit=all`).

---

## 2. Domain entities


| Entity key           | API base (current frontend)            | `recordKind`                 |
| -------------------- | -------------------------------------- | ---------------------------- |
| `incomingDocuments`  | `/api/v2/records/incoming-documents`   | `incoming`                   |
| `outgoingDocuments`  | `/api/v2/records/outgoing-documents`   | `outgoing`                   |
| `documents`          | `/api/v2/records/documents`            | `document`                   |
| `masterListRequests` | `/api/v2/records/master-list-requests` | `master_list_request`        |
| `recordLogs`         | `/api/v2/records/logs`                 | audit events (not creatable) |


### Core / shared columns


| Field                              | Role                                                            |
| ---------------------------------- | --------------------------------------------------------------- |
| `title`, `status`, `stage`         | Identity + workflow. `status` is only `active                   |
| `referenceNumber`                  | Letter / scan number (Incoming / Outgoing / Document)           |
| `recordTime`, `recordTag` / `tags` | Unified record columns                                          |
| `documentType`                     | **Company name** (classification select — not record-type code) |
| `officeInCharge`                   | Involved departments as a reference array                       |
| `involvedOfficers`                 | Officer reference array                                         |
| `externalUnits`                    | Company reference array                                         |
| `details`                          | Dynamic attributes from Configuration (optional)                |


**Removed from create/edit UI (do not require on POST for these three kinds):**

- `recordFlowCode` (Record flow)
- `recordContent` free-text labeled Incoming / Outgoing / Document
- `recordTypeId` as Document type select (Incoming/Outgoing/Document kinds)

`recordKind` is still set by the route/collection (incoming vs outgoing vs document).

### Stage transition

- Valid transitions from **record type / stage template** configuration (or fixed stage list until types are wired).
- `PATCH` record with new `stage` or `POST .../transition-stage`.
- Emit activity + append **record log** row.

---

## 3. Create / edit form contracts (source of truth for UI)

Frontend builder: `orgSelectDocumentTabs` / `masterListRequestTabs` in `entities.ts`.

### 3.1 Incoming / Outgoing / Document (shared shape)


| Field                                     | UI                  | Options API                                 | Required |
| ----------------------------------------- | ------------------- | ------------------------------------------- | -------- |
| `status`                                  | select              | enum                                        | yes      |
| `title`                                   | text                | —                                           | yes      |
| `documentType`                            | select              | `GET .../companies/options?valueField=name` | yes      |
| `referenceNumber`                         | text                | —                                           | yes      |
| `letterSubject`                           | text                | —                                           | yes      |
| Date                                      | date                | —                                           | yes      |
| `directorGeneralDate`                     | date                | —                                           | no       |
| `directorDate`                            | date                | —                                           | no       |
| `officeInCharge` (label: Involved office) | mention multi-input | `GET .../departments/options`               | no       |
| `involvedOfficers`                        | mention multi-input | `GET .../officers/options`                  | no       |
| `externalUnits`                           | mention multi-input | `GET .../companies/options`                 | no       |
| `tags` / `recordTag`                      | csv-list / tags     | —                                           | no       |


**Date field by kind:**


| Kind     | Field          |
| -------- | -------------- |
| Incoming | `receivedDate` |
| Outgoing | `sentDate`     |
| Document | `documentDate` |


**Lookup and assignment:** all three fields are arrays of `{ id, label, type }` references, even for one selection. Typing `@` or normal text sends indexed `q` search with bounded `limit`; the API permission-filters results, validates tenant scope, resolves authoritative labels, and de-duplicates `(type,id)`. Cards may show labels joined by commas; UI tag colors are presentation-only.

### 3.2 Master List Request (minimal)


| Field                | UI       | Required |
| -------------------- | -------- | -------- |
| `status`             | select   | yes      |
| `title`              | text     | yes      |
| `recordTime`         | datetime | yes      |
| `tags` / `recordTag` | csv-list | no       |


No letter number, office/officer, external units, or document-type fields on this form.

---

## 4. List & board queries

### Stage board


| Query                | Meaning                                                 |
| -------------------- | ------------------------------------------------------- |
| `stage`              | Filter one stage (null = All)                           |
| `startDate`, `endDate` | Filter on resolved `recordTime`                       |
| `search` / `q`       | Title, reference, tags, org fields                      |
| `sort`               | Default by `record_time` / updated                      |
| `page`, `limit`      | Pagination; `limit=all` → large fetch (cap e.g. 10_000) |


List payloads must include card slots from App Config (`documentType`, `officeInCharge`, `involvedOfficers`, `externalUnits`, etc.).

### Record logs board


| Query                | Meaning                                                                          |
| -------------------- | -------------------------------------------------------------------------------- |
| `view`               | `all`, `created`, `updated`, `stage`, `shared`, `incoming`, `outgoing`, `errors` |
| `startDate`, `endDate` | Event time (`recordTime` / `occurredAt`)                                      |
| `search`             | Summary, entity title, actor                                                     |
| `page`, `limit`      | Including `all`                                                                  |


Log rows are **immutable**.

Lifecycle behavior is independent of `stage`: creator-scoped users may archive and restore their own archived documents; normal delete is a recoverable tombstone that only an administrator may restore; permanent purge is administrator-only and retention/legal-hold protected. Archive preserves the last stage and freezes transitions. Restore returns to that stage or a configured recovery stage. Every transition and lifecycle action creates immutable activity; comments remain available while Active/Archived and become read-only when Deleted.

---

## 5. Key operations


| Operation                         | Behavior                                                                                    |
| --------------------------------- | ------------------------------------------------------------------------------------------- |
| Create                            | `POST` collection; set `recordKind` from route; validate form fields in §3; initial `stage` |
| Update                            | `PATCH` id; validate org select values exist when using FKs                                 |
| Stage move                        | Validate transition; rollback on 409                                                        |
| Delete                            | Soft-delete / archive; permission-gated                                                     |
| Comments / activity / attachments | Shared sub-resources (§7)                                                                   |


---

## 6. Permissions (minimum)


| Code                                          | Use                     |
| --------------------------------------------- | ----------------------- |
| `records.incoming_documents.view` / `.edit`   | Incoming                |
| `records.outgoing_documents.view` / `.edit`   | Outgoing                |
| `records.documents.view` / `.edit`            | Document                |
| `records.master_list_requests.view` / `.edit` | Master list             |
| `records.logs.view`                           | Record logs (read-only) |


Also need read on Organization options used by the form (`organizations.companies.view`, `departments.view`, `officers.view`) or a dedicated options permission.

---

## 7. Shared sub-resources


| Resource    | Method   | Path pattern                            |
| ----------- | -------- | --------------------------------------- |
| Comments    | GET/POST | `/api/v2/{entityPath}/{id}/comments`    |
| Activity    | GET      | `/api/v2/{entityPath}/{id}/activity`    |
| Attachments | GET/POST | `/api/v2/{entityPath}/{id}/attachments` |


---

## 8. Activity & record logs

1. Append **activity** on the record document timeline.
2. Write **record log** for audit-grade events (stage, share, cross-module).

---

## 9. Organization dependency

Form selects consume Organization module options:


| Endpoint                                    | Used for                      |
| ------------------------------------------- | ----------------------------- |
| `/api/v2/organizations/companies/options`   | Document type, External units |
| `/api/v2/organizations/departments/options` | Involved office               |
| `/api/v2/organizations/officers/options`    | Involved officers             |


See `prompt/backend/modules/organization-master-data.md` §3 (lookup options). Support query `valueField=name` (or return both `id` + `name` and let clients choose).

---

## 10. Frontend contract (implemented)


| Concern               | Code                                                                    |
| --------------------- | ----------------------------------------------------------------------- |
| Entity + form schemas | `config/entities.ts` → `orgSelectDocumentTabs`, `masterListRequestTabs` |
| Stage board           | `useRecordStageBoard.ts`, `AppRecordStageBoard.vue`                     |
| Log board             | `useRecordLogBoard.ts`, `AppRecordLogBoard.vue`                         |
| Document page         | `useDocumentPage.ts`, `EntityDocumentView`                              |
| Reference options     | `adapters/reference-options.ts`                                         |
| Card slots            | `utils/card-fields.ts`, `useCardFields`                                 |
| Pagination All        | `utils/pagination.ts`, `AppServerTable`                                 |


**Mock → HTTP:** `NUXT_PUBLIC_USE_MOCK_DATA=false`. List date filters: `startDate` / `endDate`.

**Backend files (later):** `app/api/v2/records.py`, `app/modules/record/`, `app/modules/collaboration/`.

---

## 11. Validation summary


| Case                                      | Result    |
| ----------------------------------------- | --------- |
| Missing required form field (§3)          | 422       |
| Invalid company/department/officer option | 422 / 404 |
| Invalid stage transition                  | 422       |
| Edit without permission                   | 403       |
| Log row mutate from client                | 405       |


---

*Keep Incoming / Outgoing / Document form fields in sync with* `orgSelectDocumentTabs`*; Master List with* `masterListRequestTabs`*.*
