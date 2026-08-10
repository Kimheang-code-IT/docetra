# Docetra Backend Prompts

Backend and API **system flow** specs for each major product area. They complement `prompt/specification/` and match the implemented UI in `frontend/`.

**Product source of truth:** `prompt/idea/`, `prompt/specification/` (`06-api-contracts.md`, `07-data-model.md`, module docs).

When this folder and the engineering spec disagree on architecture or API shape, **`prompt/specification/` wins**. When the spec is silent on screen-specific behavior, these files define the intended backend contract.

---

## Module index

| Area | Doc | Routes (summary) |
| --- | --- | --- |
| **Meeting** | [`modules/meeting-topic-board.md`](./modules/meeting-topic-board.md) | `/meetings/topics`, `/meetings/history` |
| **Record** | [`modules/record-workflow-boards.md`](./modules/record-workflow-boards.md) | `/records/*` boards + logs + document pages |
| **Organization** | [`modules/organization-master-data.md`](./modules/organization-master-data.md) | `/organizations/departments`, `companies`, `company-purposes`, `company-sectors`, `officers` |
| **Portal** | [`modules/portal-operations.md`](./modules/portal-operations.md) | `/portal/file-upload`, `google-drive-sync`, `portal-logs` |
| **User management** | [`modules/user-management.md`](./modules/user-management.md) | `/user-management/roles`, `/users` |
| **Configuration** | [`modules/configuration-record-metadata.md`](./modules/configuration-record-metadata.md) | `/configuration/record-types`, `record-attributes` |
| **Settings** | [`modules/settings-application.md`](./modules/settings-application.md) | `/settings/app-info`, `app-config`, `storage` |

**Related (not duplicated here):** System Log — `/system-monitor/system-logs` (read-only audit, same list pattern as portal logs).

---

## End-to-end flow (how areas connect)

```text
Configuration (record types / attributes / stages)
        │
        ▼
Record boards & documents ◀── App Config (card fields, page size)
        │     └── form selects: companies, departments, officers
        │
        ├── Attachments ──▶ Settings (storage providers)
        │
Organization (dept / company / officer) ──▶ Record parties + User↔Officer
        │
Portal (upload / Drive sync) ──▶ Drive file catalog ──▶ Meeting notes link
        │
User Management (roles / users) ──▶ permissions on every API
        │
Settings (email / telegram / system flags) ──▶ notifications & read-only mode
```

### Record form quick reference (see record-workflow-boards.md §3)

| Kind | Create/edit fields |
| --- | --- |
| Incoming / Outgoing / Document | Status, Title, Document type (company), Letter no./subject, Date, DG/Director dates, Involved office/officers, External units, Tags — **no** Record flow / content blob |
| Master List Request | Status, Title, Record time, Record tag only |

---

## Frontend integration

- **Entity CRUD:** `frontend/app/adapters/createEntityAdapter.ts` + `config/entities.ts`
- **Configuration / Settings:** `useConfigurationRepositories()`, `useSettingsRepositories()`
- **Special boards:** `meeting-board`, `useRecordStageBoard`, `useRecordLogBoard`, `AppFileUploadBoard`
- **Toggle API:** `NUXT_PUBLIC_USE_MOCK_DATA=false` → HTTP repos and same paths in `api-endpoints.ts`

Each module doc ends with a **Frontend contract** section listing key files.

---

## Reading order for implementers

1. `prompt/specification/00-overview.md` + `02-domain-model.md`
2. This folder — module matching your feature area
3. `prompt/frontend/README.md` — route → component map
4. `prompt/specification/06-api-contracts.md` — global REST conventions
