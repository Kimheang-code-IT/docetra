# Configuration — Record Types & Attributes (Backend Logic)

> **UI scope:** Configuration nav — **Record Type**, **Record Attribute**.  
> **References:** `prompt/specification/modules/admin-config.md`, `frontend/app/config/configuration-schemas.ts`, `repositories/contracts/configuration.ts`.

---

## 1. Purpose

Configuration defines **how records behave** before operational data exists:

| Route | UI | Flow |
| --- | --- | --- |
| `/configuration/record-types` | `AppRecordTypeList` | Index + search |
| `/configuration/record-types/new`, `/:id` | `AppRecordTypeEditor` | General, features, assigned attributes, workflow, comments/activity |
| `/configuration/record-attributes` | `AppRecordAttributeList` | Index |
| `/configuration/record-attributes/new`, `/:id` | `AppRecordAttributeEditor` | Field definition + builders |

Changes here drive:

- **Workflow stages** and optional extra attribute tabs on records (`useRecordTypeDrivenTabs`).
- Validation and visibility for assigned attributes on save.
- Stage lists on Incoming / Outgoing / Document / Master List boards.

**Current UI:** Record and Meeting add/detail/edit pages resolve assigned fields through the Record Type schema boundary. Core identity/workflow fields can remain protected, but user-defined Attribute Catalog fields are not copied into page code. Mock mode exercises the same assignment, stage, visibility, and `details` payload contracts expected from HTTP.

Configuration is capability-restricted. The current frontend release uses localStorage-backed mock repositories; the later API release sets `NUXT_PUBLIC_USE_MOCK_DATA=false` and uses the existing HTTP repository contracts.

---

## 2. Domain entities

### Record type

| Field | Role |
| --- | --- |
| `id`, `name`, `code` | Identity; `code` stable for API |
| `status` | `active` / `archived` / `deleted` business lifecycle |
| `publicationState` | Optional separate `draft` / `published` metadata lifecycle |
| `workflowStages` | Ordered stages + transitions |
| `numberingRule` | Reserved API-compatible numbering metadata; the current editor intentionally has no Numbering tab |
| `assignedAttributeIds` | Many-to-many to attributes |
| `recordTimePriority` | Which field resolves `record_time` |

### Record attribute

| Field | Role |
| --- | --- |
| `id`, `name`, `code` | `code` used in `record_detail` |
| `dataType` | text, number, date, select, etc. |
| `options` | Enum values (options builder) |
| `validationRules` | min/max/required/custom |
| `visibilityRules` | show/hide based on other fields |
| `status` | `active` / `archived` / `deleted` business lifecycle |

### Relationship

```text
RecordType ──assigned──▶ RecordAttribute (many)
Record (runtime) ──recordTypeId──▶ RecordType
Record.detail[attribute.code] ──▶ value
```

---

## 3. Admin flows

### Create attribute

1. Define code, label, type, options/validation/visibility builders.
2. Save → available for assignment on types.
3. Inactive attributes hidden on new records; existing values preserved.

### Create / edit record type

1. General/features fields + workflow stage builder. Numbering metadata may round-trip for API compatibility but is not currently edited in a tab.
2. Assign attributes (sort order for form sections).
3. Save → record boards and document forms pull catalog on next load.

### Impact on running system

| Change | Runtime behavior |
| --- | --- |
| Disable attribute | Hide on forms; keep stored values |
| Disable type | Block new records; existing remain readable |
| Change workflow | New transitions validated; invalid current stage flagged |

Version stamp optional: `settings.app_config.configurationVersion` for cache bust.

---

## 4. API surface (proposed)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v2/configuration/record-types` | List (paginated) |
| GET | `/api/v2/configuration/record-types/{id}` | Detail |
| POST | `/api/v2/configuration/record-types` | Create |
| PATCH | `/api/v2/configuration/record-types/{id}` | Update |
| GET | `/api/v2/configuration/record-types/{id}/schema` | Permission-filtered published runtime schema |
| GET | `/api/v2/configuration/record-types/by-code/{code}/schema` | Resolve schema for record-backed routes |
| GET | `/api/v2/configuration/record-attributes` | List |
| GET | `/api/v2/configuration/record-attributes/{id}` | Detail |
| POST | `/api/v2/configuration/record-attributes` | Create |
| PATCH | `/api/v2/configuration/record-attributes/{id}` | Update |
| GET/POST | `/api/v2/configuration/record-types/{id}/comments` | Cursor-paginated comments |
| GET | `/api/v2/configuration/record-types/{id}/activity` | Cursor-paginated immutable activity |
| GET/POST | `/api/v2/configuration/record-attributes/{id}/comments` | Cursor-paginated comments |
| GET | `/api/v2/configuration/record-attributes/{id}/activity` | Cursor-paginated immutable activity |

Optional: `GET /record-types/{id}/attributes` expanded catalog for document page bootstrap.

---

## 5. Validation

| Case | Result |
| --- | --- |
| Duplicate `code` | 409 |
| Circular visibility rules | 422 |
| Invalid workflow transition | 422 |
| Delete attribute assigned to type | 409 or force-unassign |
| Data type mismatch on runtime record save | 422 from record module |

---

## 6. Permissions

| Code | Use |
| --- | --- |
| `configuration.record_types.view` / `.create` / `.edit` / `.delete` / `.comment` / `.configure` | Record types |
| `configuration.record_attributes.view` / `.create` / `.edit` / `.delete` / `.comment` / `.configure` | Attributes |

---

## 7. Frontend contract

| Concern | Code |
| --- | --- |
| Schemas | `config/configuration-schemas.ts` |
| Types | `types/docetra/configuration.ts` |
| Repositories | `useConfigurationRepositories()` — mock + HTTP |
| Builders | `AppWorkflowStageBuilder`, `AppAttributeOptionsBuilder`, `AppValidationRuleBuilder`, `AppVisibilityRuleBuilder` |
| List composable | `useConfigListPage.ts` |
| Runtime merge | `useRecordTypeDrivenTabs.ts`, `utils/record-type-fields.ts` |
| Endpoints | `RECORD_TYPES`, `RECORD_ATTRIBUTES` |

**Mock keys:** `docetra:config:record-types`, `docetra:config:record-attributes` in localStorage.

**Backend files:** `backend/app/api/v2/configuration.py`, `backend/app/modules/record/validation.py`.

List query uses `startDate`/`endDate`. Lifecycle: archive/restore/soft-delete/purge on the entity adapter.

---

## 8. Dependency boundaries

- **Does not** store operational record rows.
- **Does not** execute workflow moves (record module does).
- **Feeds** record module, reporting, and card-field labels (via i18n + attribute labels).

---

*Document types as separate entities may merge into record types per product; current UI uses unified record type only.*
