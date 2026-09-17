# Docetra — Configuration (Record Types, Attribute Catalog, Settings)

Verified implementation: `modules/record/api/configuration.py`, `modules/record/services/configuration.py`, `modules/admin_config/*`, `/configuration/*` and `/settings/*` pages.

## Record Types (`/configuration/record-types`)

- CRUD + `duplicate`, `bulk-delete`, `archive/restore/purge`, per-type `permissions` (organization × permission_kind), `schema` (by id and by code), comments/activity/attachments/neighbors, `counts`, `options`.
- Editor components: `AppRecordTypeEditor`, `AppWorkflowStageBuilder` (stage list with colors, initial/final flags, ordering), `AppValidationRuleBuilder`, `AppVisibilityRuleBuilder`, `AppNumberingPreview` (prefix-based reference numbers).
- Type record: `code` (unique, stable, pattern `^[a-z][a-z0-9_]{1,63}$`, reserved segments `_meta|logs|schema`), `name`, `description`, `payload` JSON:
  - `uiSurface` (meeting | document | system), `slug`, `icon`, `menuOrder`, `isCreatable`, `supportsStages`, `supportsTopicContainer`, `features` (allowAttachments, allowComments, allowAssignment, enableWorkflow, enableDueDate, enableHistory, enableExport…).
- Built-in types auto-seed (`resolve_or_ensure_type`): meeting_topic, meeting_history, document, incoming_document, outgoing_document, master_list_request — with UI defaults and numbering prefixes (TPC/MTG/DOC/INC/OUT/MLR).
- Seeding a new type registers its permission prefix automatically (`configure_record_permissions` → catalog refresh) — the frontend role matrix and menus pick it up with no deploy.

## Attribute Catalog (`/configuration/record-attributes`)

- Reusable field definitions: `code` (unique), `name`, `data_type` (text, textarea, number, date, datetime, boolean, select, csv-list, url, image…), `payload` (options list, validation rules, visibility rules).
- Editor: `AppRecordAttributeEditor`, `AppAttributeOptionsBuilder` (option value/label/color/ordering).
- Mapping to types: `record_template` (record_type_id, record_attribute_id, ordering, is_require) — one attribute can serve many record types (usage counts shown in UI).
- Values stored per record in `record_detail` typed columns (value_string/number/time/boolean/json/id).
- Record schema endpoint (`GET /records/{type}/schema`, `/configuration/record-types/by-code/{code}/schema`) composes type + attributes + stages + features into the form/board renderer contract.

## Per-type workflow stages

`record_stage_template` rows (ordering, name, is_final). Document defaults: 10 stages ending `finished_final`; meeting defaults: intake/review/approval/completed. Editable via the stage builder; stage transitions validated against the type's stages.

## Record Type × Organization permissions

`record_type_permission` (record_type_id, organization_id, permission_kind) — grants/restricts type usage per department/company; managed from the record type editor.

## Settings (`/settings/*`)

| Page | Endpoint | Content |
|---|---|---|
| App Info | `GET/PUT /settings/app-info`, `POST .../reset` | `settings` key/value table (app name, logo, branding) |
| App Config | `GET/PATCH /settings/app-config` | `setting` table (key_group/key): SMTP, Telegram bots, session policy (`sessionTimeoutMinutes`), feature flags; `test-connection`/`send-test` for email + telegram |
| Storage | `/settings/storage` CRUD | storage providers (see FILE_STORAGE.md) |

- `public_access`/`visible` flags on `setting` control exposure.
- Frontend composables: `useAppBranding` (app info), `useAppLocalization`, `useAppRuntimeConfig` (bootstrap config), `useCardFields`.

## Rules

- Codes stable once adopted — rename breaks contracts and existing records.
- Configuration changes audited; limited to CONFIG/SETTINGS permissions.
- Disabled (`is_active=false`) types/attributes must not be used for new records.
- Backward compatibility required when changing config affecting existing records.
- ⚠ Frontend constants reference `GET/POST/PATCH/DELETE /configuration/enums...` — **no backend routes exist** (vocabulary API removed in migration 0011). Dead constants; see GAP_ANALYSIS.
