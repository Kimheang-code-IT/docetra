# docetra-admin-config

## Purpose

Use when implementing or modifying system-level configuration: record types, record attributes, record templates, document types, application settings, and enum-style reference data. This module is Docetra's product-behavior control layer.

## Source Documents

- docs/specification/modules/admin-config.md

## Domain Overview

Admin configuration stores configurable metadata that drives product behavior for other modules. It owns definitions — not runtime workflow logic. Runtime record workflow logic MUST NOT live in this module.

## Key Entities

| Entity | Responsibility |
|---|---|
| Record type | Defines the behavior, attributes, and workflow shape of a record |
| Record attribute | A configurable field used by one or more record types |
| Record template | Maps record types to their allowed/required attributes |
| Setting | Configurable application value used by runtime logic or other modules |
| Document type | Specialized classification for document-related records |
| Enum | Enum-style reference data where the product needs configurable classification values ("may support" — optional) |

## Relationships

- Record template maps Record type ↔ Record attribute (including which fields are required).
- Record types are consumed by the record module to drive record behavior.
- Settings may be consumed by any module as configuration values.

## Business Rules

- Configuration MUST be explicit and auditable.
- Configuration changes MUST be limited to authorized users.
- Record type and attribute codes MUST remain stable once adopted (prefer stable codes over changing labels).
- New behavior SHOULD be introduced through configuration instead of hardcoding.
- Disabled configuration MUST NOT be used incorrectly (e.g., disabled record types should not be selectable for new records).
- The module MUST NOT contain runtime record workflow logic.
- Preserve backward compatibility when changing configuration that affects existing records.

`Specification conflict:` `record_type`, `record_attribute`, and `record_template` are claimed as owned data in BOTH admin-config.md ("Data ownership") and record.md ("Data ownership"). The docs do not resolve which module is the single canonical owner. Do not move or duplicate ownership without user confirmation. `Needs verification`.

## Permissions

- Configuration changes: authorized users only (exact roles/permission codes: `Needs verification`).
- The module may depend on people_access for administrative permissions.

## Implemented Behavior (verified in code)

- **Record types**: `/configuration/record-types` (+ new/[id]) with `AppRecordTypeEditor`/`AppRecordTypeList`, plus `AppWorkflowStageBuilder` (per-type steps), `AppValidationRuleBuilder`, `AppVisibilityRuleBuilder`, `AppNumberingPreview` — dynamic fields and workflow steps are configured here, not hardcoded.
- **Attribute catalog**: `/configuration/record-attributes` (+ new/[id]) with `AppRecordAttributeEditor`/`AppAttributeOptionsBuilder`. Attributes form a reusable catalog mapped to record types via record templates (backend `record_attribute` + `record_template`).
- **Settings**: `/settings/app-config`, `/settings/app-info`, `/settings/storage`; composables `useAppBranding`, `useAppLocalization`, `useAppRuntimeConfig`, `useCardFields`.
- Built-in record types auto-seed with UI defaults via `resolve_or_ensure_type` (see docetra-record skill).

## API Rules

The module SHOULD expose APIs for:

- Record type: list, detail, create, update; record type disabling.
- Record attribute: list, detail, create, update.
- Record template: attribute mapping (with required-field definitions).
- Document type: management/maintenance.
- Setting: list and update.
- Enum: lookup and maintenance where enabled.

Exact routes, payloads, and status codes: `Needs verification` (06-api-contracts.md was not provided).

## Data Rules

Module owns or primarily manages: `record_type`, `record_attribute`, `record_template`, `document_type`, `setting`, `enum`.

- Codes MUST be unique where required.
- Configuration references (e.g., template → attribute) MUST be valid.
- Required mappings (template definitions) MUST be complete.
- Settings MUST comply with datatype and visibility rules; settings carry visibility and access-control metadata.

## Validation Rules

- Unique codes where required.
- Valid configuration references.
- Complete required mappings.
- Disabled configuration is not used incorrectly.
- Setting datatype + visibility compliance.
- Identifier format rules where applicable.

## Edge Cases

- Changing a record type/attribute that existing records already use → backward compatibility MUST be preserved. (Derived from specification: "Preserve backward compatibility when changing configuration that affects existing records.")
- Disabling a record type that still has active records. `Needs verification` for exact behavior.

## Implementation Guidance

- Keep configuration models clean and extensible.
- Treat the module as a behavior control layer: definition/storage of config, never execution of workflows.
- Avoid coupling UI names tightly to internal storage names.
- Make configuration changes auditable.

## DO NOT

- DO NOT implement record workflow execution here.
- DO NOT rename or repurpose adopted record type / attribute codes.
- DO NOT hardcode product behavior that should be configuration.
- DO NOT bypass permission checks on configuration changes.

## Testing Checklist

- [ ] Authorized user can create/update record types, attributes, templates, settings.
- [ ] Unauthorized user is denied configuration changes.
- [ ] Duplicate codes are rejected where uniqueness is required.
- [ ] Invalid references (e.g., template pointing to nonexistent attribute) are rejected.
- [ ] Disabled record types/attributes are not usable for new records.
- [ ] Adopted codes remain stable across updates.
- [ ] Configuration changes are auditable.
- [ ] Incomplete required mappings are rejected.

## Needs Verification

- Canonical owner of record_type / record_attribute / record_template (conflict with record.md).
- Exact permission codes for admin operations.
- Exact API contracts (routes, pagination, error shapes).
- Exact enum support scope ("may support" is optional in the spec).
