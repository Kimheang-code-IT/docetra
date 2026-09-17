# Docetra v2 Data Model

## Purpose

This document defines the database-level data model for Docetra v2. It describes the core entities, their responsibilities, and the structural expectations for a clean implementation.

## Data model principles

- Use PostgreSQL as the source of truth.
- Keep tables aligned with domain boundaries.
- Preserve history and auditability.
- Prefer explicit foreign keys over implicit relationships.
- Keep dynamic record data structured and queryable where possible.
- Avoid unnecessary duplication unless it supports performance or search.

## Shared base fields

Most major tables should include shared lifecycle fields where appropriate:
- `id`
- `created_at`
- `updated_at`
- `created_by`
- `updated_by`

The exact type and constraint details should be finalized in module-level schema documents.

## Core entity groups

The main database groups are:
- records.
- organizations.
- people and access.
- storage.
- configuration.
- audit and history.
- reporting support.

## Record tables

### record
Primary table for the unified record model.

Typical responsibilities:
- core record identity.
- title.
- type reference.
- status.
- current stage.
- timestamps.
- parent or linked record reference.
- workflow metadata.

#### Record time behavior

`record_time` is configurable rather than fixed to one column. The system chooses it from a priority list stored in enum or metadata configuration, using the first valid candidate field. When users view a mixed timeline without a specific record type, the system sorts by `record_time`, and that field should be indexed for performance.

### record_detail
Stores dynamic attribute values for a record.

Typical responsibilities:
- attribute code reference.
- typed value columns.
- flexible record-specific data.

### record_attachment
Stores relationships between records and related record references or attached entities.

### record_organization
Stores relationships between records and organizations.

### record_stage_template
Defines valid workflow stages for each record type.

### record_type
Defines the category and behavior of a record.

### record_attribute
Defines available attribute definitions.

### record_template
Maps record types to supported attributes.

## Organization tables

### organization
Stores departments, companies, and government structures.

Typical responsibilities:
- organization name.
- organization type.
- hierarchy.
- sector.
- purpose.
- contact information.
- identifiers.
- visibility flags.

### organization_sector
Stores sector classification data.

### organization_purpose
Stores purpose classification data.

## People and access tables

### officer
Stores the business-side person entity.

Typical responsibilities:
- officer identity.
- organization reference.
- role reference.
- account linkage.
- profile data.

### users
Stores authentication identity data if the auth system requires a local table or mirror table.

### role
Stores role definitions.

### permission
Stores permissions assigned to roles or access structures.

### menu
Stores navigation and action codes used by permissions.

### role_permission
Stores role-to-permission mapping.

## Storage tables

### file
Stores file metadata and storage reference information.

Typical responsibilities:
- file name.
- path.
- storage type.
- mime type.
- file size.
- status.
- direct URL or storage pointer.

## Configuration tables

### setting
Stores configurable application settings.

### document_type
Stores document type definitions.

### enum
Stores configurable enum-style values where required by the product.

## Audit and history tables

### audit_log
Stores immutable audit records for significant actions.

Typical responsibilities:
- action code.
- table name.
- row ID.
- actor.
- timestamp.
- request context.
- status.
- message and details.

### notification_audit_log
Stores notification processing state linked to audit activity if used by the runtime.

## Reporting tables or views

The system may use reporting tables, materialized views, or read models if necessary for performance or export support.

These should:
- remain read-oriented.
- avoid being the primary source of truth.
- be derived from core domain tables when possible.

## Data relationship rules

- Every record must reference a valid record type.
- Every record must be linked to an organizational context.
- Every dynamic record detail must map to a valid attribute definition.
- Every permission must be tied to a role or an equivalent access entity.
- Every audit row should map to a tracked action and target entity.

## Data integrity expectations

The schema should enforce:
- foreign key consistency.
- uniqueness where appropriate.
- required record classification.
- safe deletion behavior.
- history preservation where records are tracked over time.

## Indexing expectations

The implementation should index:
- record type.
- record status.
- record stage.
- organization references.
- permission lookup fields.
- audit lookup fields.
- search-oriented fields such as title and code.

## Migration and evolution

The schema should support later growth without major restructuring.

Preferred evolution rules:
- add new record types without changing the core record table.
- add new attributes through configuration rather than schema changes where practical.
- preserve historical rows rather than overwriting them.
- keep future workflow expansion compatible with the current model.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `02-domain-model.md`
- `03-functional-requirements.md`
- `04-permissions-and-access.md`
- `modules/record.md`
- `modules/organization.md`
- `modules/people-access.md`
- `modules/admin-config.md`
