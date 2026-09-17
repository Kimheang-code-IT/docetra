# docetra-specification

## Purpose

Primary source-of-truth skill for Docetra v2. Load this before implementing, changing, or reviewing any Docetra feature. It tells the agent how to use the specification skills and what rules apply across all modules.

## Source Documents

- docs/specification/modules/admin-config.md
- docs/specification/modules/organization.md
- docs/specification/modules/people-access.md
- docs/specification/modules/record.md
- docs/specification/modules/reporting-support.md
- docs/specification/modules/storage-integration.md

Only these module documents were used. The shared specification files (`00-overview.md` ... `10-migration-notes.md`) exist in the repository but were NOT provided for this skill — treat their content as `Needs verification`.

## Global Rules

- The Docetra specification is the primary source of truth.
- Consult the relevant module skill (or the module doc itself) BEFORE implementing a feature in that module.
- Existing code MUST NOT override explicit specification requirements unless the user explicitly states the code is newer.
- Do NOT invent missing behavior, entities, fields, permissions, statuses, or API contracts. Mark gaps as `Needs verification`.
- Keep terminology exactly as defined in the docs: `record`, `record type`, `record stage`, `record detail`, `record attachment`, `record organization link`, `officer`, `user account`, `role`, `permission`, `access context`, `organization`, `sector`, `purpose`, `file`, `storage object`, `sync source`, `reporting dataset`, `read model`, `setting`, `record template`, `document type`.
- Check permissions + API + data + workflow TOGETHER when implementing any feature.
- Respect cross-module dependency boundaries (see below).

## Documentation Lookup Guide

| Need | File |
|---|---|
| Admin configuration (record types, attributes, templates, settings, enums, document types) | docs/specification/modules/admin-config.md |
| Organizations, hierarchy, sectors, purposes, history | docs/specification/modules/organization.md |
| Officers, users, roles, permissions, access context | docs/specification/modules/people-access.md |
| Records, stages, dynamic attributes, attachments, meetings, history | docs/specification/modules/record.md |
| Exports, dashboards, read models, reporting | docs/specification/modules/reporting-support.md |
| File upload, file metadata, object storage, Google Drive sync | docs/specification/modules/storage-integration.md |
| Implemented product behavior (routes, components, entity configs, verified in code) | docs/specification/product-features.md |

`product-features.md` is the frontend-verified behavior reference: record surfaces (meeting_topic, meeting_history, document, incoming_document, outgoing_document, master_list_request), meeting topic containers, document flows, departments/companies/officers usage, portal, users/roles, configuration. Consult it for how features work today; module specs remain authoritative for domain rules.

Shared standards, API contracts, data model, user flows, permissions matrix, implementation plan, and migration notes: `Needs verification` — module docs reference `00-overview.md`, `01-system-architecture.md`, `02-domain-model.md`, `03-functional-requirements.md`, `04-permissions-and-access.md`, `06-api-contracts.md`, `07-data-model.md`, but these were not provided for skill generation. Do not guess their contents; read them directly if the task requires them.

## Cross-Module Dependency Rules (from module docs)

Allowed dependency directions stated by the docs:

- ALL modules may depend on `people_access` for permission checks.
- `record` may depend on: `people_access` (permissions/identity), `organization` (organization references), `storage_integration` (file linkage), `admin_config` (types and attributes).
- `organization` may depend on: `people_access`, `record` (record-to-organization relationships, if needed), `admin_config` (if sector/purpose become configurable).
- `admin_config` may depend on: `people_access` (admin permissions), `record` (record-type behavior consumption), `organization` (if config becomes organization-linked), `reporting_support` (if config values appear in admin reports).
- `storage_integration` may depend on: `record` (attachment/linkage), `people_access` (permission checks), `admin_config` (storage configuration), `reporting_support` (file inventory reporting, if needed).
- `reporting_support` may depend on: `record`, `organization`, `people_access`, `admin_config`.
- `people_access` may depend on: `organization` (department/company context), `record` (record-specific access checks), `admin_config` (configurable access rules, if needed).

`Specification conflict:` The docs state several mutual ("may depend on") pairs that form potential cycles: record ↔ admin_config, record ↔ storage_integration, record ↔ organization, and organization ↔ admin_config. The docs do not define which direction is authoritative. When implementing, prefer the direction implied by data ownership (the owner module is the dependency target) and flag any cycle to the user. Do not resolve this silently. (See also `Specification conflict` on record_type ownership below.)

## Universal Invariants

- Backend authorization is the source of truth; access MUST NOT depend solely on frontend state (people-access.md).
- History/traceability MUST be preserved for organization and record changes.
- Sensitive/unauthorized data MUST NOT appear in reports or exports.
- Binary file content MUST be stored outside the database; file metadata MUST be stored in PostgreSQL.
- Record type and attribute codes MUST remain stable once adopted.
- Configuration must be explicit and auditable; prefer configuration over hardcoding for new behavior.

## DO NOT

- DO NOT invent statuses, permissions, fields, or endpoints not present in the specs.
- DO NOT rename domain terms (record, officer, stage, sector, purpose, etc.).
- DO NOT move data ownership between modules without explicit user approval.
- DO NOT mix business workflow logic into admin_config, storage_integration, or reporting_support (docs forbid it).
- DO NOT implement authorization in frontend code or duplicate access rules in controllers/UI.
- DO NOT delete history/audit data.

## Needs Verification

- Exact permission catalog and role matrix (module docs name the concept, not the codes).
- Exact API routes, request/response shapes, pagination conventions.
- Exact database schemas, column definitions, nullability.
- System-wide architecture standards, shared error handling, migration strategy.
