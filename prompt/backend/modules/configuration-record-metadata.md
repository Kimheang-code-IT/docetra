# Configuration — Record Types & Attributes (Backend Logic)

> **UI scope:** Configuration nav — **Record Type**, **Record Attribute**.  
> **References:** `prompt/specification/modules/admin-config.md`, `frontend/app/config/configuration-schemas.ts`, `repositories/contracts/configuration.ts`.

---

## 1. Purpose

Configuration defines **how records behave** before operational data exists:

| Route | UI | Flow |
| --- | --- | --- |
| `/configuration/record-types` | `AppRecordTypeList` | Index + search |
| `/configuration/record-types/new`, `/:id` | `AppRecordTypeEditor` | Workflow, numbering, assigned attributes |
| `/configuration/record-attributes` | `AppRecordAttributeList` | Index |
| `/configuration/record-attributes/new`, `/:id` | `AppRecordAttributeEditor` | Field definition + builders |

Changes here drive:

- **Workflow stages** and optional extra attribute tabs on records (`useRecordTypeDrivenTabs`).
- Validation and visibility for assigned attributes on save.
- Stage lists on Incoming / Outgoing / Document / Master List boards.

**Note (current UI):** Base create/edit fields for Incoming / Outgoing / Document are **fixed** in `orgSelectDocumentTabs` (company/department/officer selects) — not the old Record flow / record-type document-type picker. Master List Request base form is only status, title, `recordTime`, tags. Configuration still owns stages and any *additional* type-driven fields.

Configuration is **admin-only**; mock today uses localStorage repositories; production uses HTTP.

---

## 2. Domain entities

### Record type

| Field | Role |
| --- | --- |
| `id`, `name`, `code` | Identity; `code` stable for API |
| `status` | active / draft / disabled |
| `workflowStages` | Ordered stages + transitions |
| `numberingRule` | Prefix/pattern preview |
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
| `status` | active / disabled |

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

1. Base fields + workflow stage builder + numbering preview.
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
| GET | `/api/v2/configuration/record-attributes` | List |
| GET | `/api/v2/configuration/record-attributes/{id}` | Detail |
| POST | `/api/v2/configuration/record-attributes` | Create |
| PATCH | `/api/v2/configuration/record-attributes/{id}` | Update |

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
| `configuration.record_types.view` / `.edit` | Record types |
| `configuration.record_attributes.view` / `.edit` | Attributes |

---

## 7. Frontend contract

| Concern | Code |
| --- | --- |
| Schemas | `config/configuration-schemas.ts` |
| Types | `types/docetra/configuration.ts` |
| Repositories | `useConfigurationRepositories()` — mock + HTTP |
| Builders | `AppWorkflowStageBuilder`, `AppAttributeOptionsBuilder`, `AppValidationRuleBuilder`, `AppVisibilityRuleBuilder`, `AppNumberingPreview` |
| List composable | `useConfigListPage.ts` |
| Runtime merge | `useRecordTypeDrivenTabs.ts`, `utils/record-type-fields.ts` |
| Endpoints | `RECORD_TYPES`, `RECORD_ATTRIBUTES` |

**Mock keys:** `docetra:config:record-types`, `docetra:config:record-attributes` in localStorage.

---

## 8. Dependency boundaries

- **Does not** store operational record rows.
- **Does not** execute workflow moves (record module does).
- **Feeds** record module, reporting, and card-field labels (via i18n + attribute labels).

---

*Document types as separate entities may merge into record types per product; current UI uses unified record type only.*
