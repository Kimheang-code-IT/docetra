# Docetra v2 Module: Admin Configuration

## Purpose

The admin configuration module manages system-level configuration data in Docetra v2, including record types, record attributes, document types, settings, and other configurable metadata that drives product behavior.

## Module responsibilities

The admin configuration module owns:
- record type definitions.
- record attribute definitions.
- record templates.
- document type definitions.
- application settings.
- enum-style configuration data.
- visibility and access flags for settings.
- configurable metadata used by other modules.

## Core concepts

### Record type
A record type defines the behavior, attributes, and workflow shape of a record.

### Record attribute
A record attribute defines a configurable field used by one or more record types.

### Record template
A record template maps record types to their allowed or required attributes.

### Setting
A setting is a configurable application value used by runtime logic or other modules.

### Document type
A document type is a specialized classification used for document-related records.

## Functional behavior

### Record type management
The module must support creating, updating, listing, and disabling record types.

### Record attribute management
The module must support creating and managing record attributes.

### Record template management
The module must support mapping attributes to record types and defining required fields.

### Document type management
The module must support document type definitions and maintenance.

### Setting management
The module must support configuration value management with visibility and access control metadata.

### Enum-style data support
The module may support enum-style reference data where the product needs configurable classification values.

## Data ownership

The admin configuration module should own or primarily manage:
- `record_type`
- `record_attribute`
- `record_template`
- `document_type`
- `setting`
- `enum`

## Key validations

The module should validate:
- codes are unique where required.
- configuration references are valid.
- required mappings are complete.
- disabled configuration is not used incorrectly.
- settings comply with datatype and visibility rules.

## API responsibilities

The module should expose APIs for:
- record type list and detail.
- record type create and update.
- record attribute list and detail.
- record attribute create and update.
- record template mapping.
- document type management.
- setting list and update.
- enum lookup and maintenance where enabled.

## Dependency boundaries

The module may depend on:
- people_access for administrative permissions.
- record for record-type behavior consumption.
- organization if certain configurable values become organization-linked.
- reporting_support if configuration values must appear in administrative reports.

The module should not contain runtime record workflow logic itself.

## Configuration rules

- Configuration must be explicit and auditable.
- Changes to configuration should be limited to authorized users.
- Record type and attribute codes should remain stable once adopted.
- New behavior should be introduced through configuration where practical instead of hardcoding.

## Implementation notes

- Keep configuration models clean and extensible.
- Prefer stable codes over changing labels.
- Treat this module as a product behavior control layer.
- Avoid coupling UI names too tightly to internal storage names.
- Preserve backward compatibility when changing configuration that affects existing records.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `02-domain-model.md`
- `03-functional-requirements.md`
- `04-permissions-and-access.md`
- `07-data-model.md`
- `modules/record.md`
- `modules/people-access.md`
