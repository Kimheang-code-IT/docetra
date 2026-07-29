# Docetra v2 Module: Organization

## Purpose

The organization module manages organizational entities in Docetra v2, including departments, companies, and government structures. It provides the organizational context used for ownership, collaboration, visibility, and history tracking.

## Module responsibilities

The organization module owns:
- organization records.
- organization hierarchy.
- organization sector and purpose metadata.
- organization history.
- organization identifiers and contact details.
- organization lookup for record relationships.
- classification data used by the rest of the system.

## Core concepts

### Organization
An organization is a business or administrative entity in the system. It may represent a department, company, government unit, or related structure.

### Organization hierarchy
An organization may have a parent-child structure to model reporting lines or grouped structures.

### Sector
A sector classifies an organization by category or industry grouping.

### Purpose
A purpose describes why the organization exists in the system or how it is used operationally.

## Functional behavior

### Organization creation
The module must support creation of organizations with core metadata such as:
- name.
- type.
- hierarchy.
- sector.
- purpose.
- contact information.
- identifiers.
- status.

### Organization update
The module must support editing organization metadata while preserving traceability.

### Organization hierarchy management
The module must support parent-child relationships and related hierarchy updates.

### Organization history
The module must preserve historical changes for organization records.

### Organization lookup
The module must provide organization lookup data for other modules, especially record management and access control.

## Supported organization types

The system should support at least:
- department.
- company.
- government structure.

The design should allow additional organization types later if needed.

## Key validations

The module should validate:
- organization name is present.
- organization type is valid.
- hierarchy does not create invalid cycles.
- sector and purpose references are valid.
- status changes are allowed.
- identifier fields meet required format rules where applicable.

## Data ownership

The organization module should own or primarily manage:
- `organization`
- `organization_sector`
- `organization_purpose`

If history is stored in a separate table or event stream, the module should still own its behavior.

## API responsibilities

The module should expose APIs for:
- organization list.
- organization detail.
- organization create.
- organization update.
- organization hierarchy retrieval.
- organization history retrieval.
- lookup and search endpoints for other modules.

## Dependency boundaries

The organization module may depend on:
- people_access for permission checks.
- record for record-to-organization relationships if needed.
- admin_config for configurable reference data if sector or purpose become configurable.

The module should not contain record-specific workflow logic.

## Relationship to other modules

### Record
Records may link to organizations for ownership, participation, or visibility.

### People and access
Officers may belong to organizations, and access control may depend on organization scope.

### Reporting support
Organization data should be available for operational reporting and filtering.

## Implementation notes

- Keep hierarchy logic explicit and cycle-safe.
- Preserve history for organization changes.
- Keep lookups fast and stable.
- Use shared classification models consistently across the system.
- Avoid mixing organization metadata with record workflow logic.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `02-domain-model.md`
- `03-functional-requirements.md`
- `04-permissions-and-access.md`
- `07-data-model.md`
- `modules/record.md`
- `modules/people-access.md`
