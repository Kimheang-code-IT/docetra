# docetra-organization

## Purpose

Use when implementing or modifying organizations, organization hierarchy, sectors, purposes, organization history, or organization lookup used by other modules.

## Source Documents

- docs/specification/modules/organization.md

## Domain Overview

The organization module manages organizational entities (departments, companies, government structures) and provides the organizational context used across Docetra for ownership, collaboration, visibility, and history tracking. It must not contain record-specific workflow logic.

## Key Entities

| Entity | Responsibility |
|---|---|
| Organization | Business/administrative entity: department, company, government unit, or related structure |
| Organization hierarchy | Parent-child structure modeling reporting lines or grouped structures |
| Sector | Classifies an organization by category or industry grouping |
| Purpose | Describes why the organization exists in the system / how it is used operationally |
| Organization history | Historical changes for organization records |

## Relationships

- Organization → parent Organization (hierarchy).
- Organization → Sector (classification), Organization → Purpose (operational role).
- Records may link to organizations (ownership, participation, visibility) — record module side.
- Officers may belong to organizations; access control may use organization scope — people_access side.
- Reporting uses organization data for summaries and filtering.

## Business Rules

- Organization metadata edits MUST preserve traceability (history).
- Hierarchy MUST be cycle-safe; invalid cycles MUST be rejected.
- Supported organization types MUST include at least: department, company, government structure; design MUST allow additional types later.
- Lookup data for other modules (especially record management and access control) MUST be fast and stable.
- Shared classification models (sector, purpose) MUST be used consistently across the system.
- The module MUST NOT contain record-specific workflow logic.

## Permissions

- Permission checks come from people_access. Exact role/permission codes: `Needs verification`.

## State / Workflow Rules

- No workflow states are defined in the doc beyond `status` being part of organization metadata and "status changes are allowed" being a validation concern. Exact status values/transitions: `Needs verification`.

## API Rules

The module SHOULD expose APIs for:

- Organization: list, detail, create, update.
- Hierarchy retrieval.
- History retrieval.
- Lookup and search endpoints for other modules.

Exact routes, payloads, pagination: `Needs verification`.

## Data Rules

Module owns or primarily manages: `organization`, `organization_sector`, `organization_purpose`.

- Organization core metadata includes: name, type, hierarchy (parent), sector, purpose, contact information, identifiers, status.
- If history is stored in a separate table or event stream, the organization module still owns its behavior.

## Validation Rules

- Name MUST be present.
- Type MUST be valid (at minimum department/company/government structure).
- Hierarchy MUST NOT create invalid cycles.
- Sector and purpose references MUST be valid.
- Status changes MUST be allowed (i.e., validated as legal).
- Identifier fields MUST meet required format rules where applicable.

## Edge Cases

- Creating a hierarchy cycle (org A parent of B parent of A) → MUST be rejected. (Derived from specification: "hierarchy does not create invalid cycles".)
- Reparenting an organization with descendants → history must capture the change and cycle check must still apply. (Derived from specification.)

## Implemented Behavior (verified in code)

- **Departments**: `/organizations/departments` (+ new/[id]), entity `departments`, permission `organizations.departments.view`. Backend `organization` model supports parent-child hierarchy (main department → sub-departments). Departments are selected via @mention (`Type @ or a department name ...`) as `internalUnits` when creating meetings/documents.
- **Companies**: `/organizations/companies` (+ dynamic `/organizations/[orgType]`). Companies attach to meetings/records via `externalUnits` / `senderOrganization` selects.
- **Sector / Purpose**: reusable classification forms at `/sector` and `/purpose`; company forms select from them. Shared classification models MUST be used consistently.

## Implementation Guidance

- Keep hierarchy logic explicit and cycle-safe.
- Preserve history for all organization changes.
- Keep lookup endpoints fast and stable for cross-module consumption.
- Do not mix organization metadata with record workflow logic.

## DO NOT

- DO NOT implement record workflow logic in this module.
- DO NOT break hierarchy invariants (cycles, orphaned parents) — check before mutation.
- DO NOT skip history preservation on updates.
- DO NOT invent new organization types beyond department/company/government structure without making type support configurable/extensible.

## Testing Checklist

- [ ] Organization can be created with name, type, hierarchy, sector, purpose, contacts, identifiers, status.
- [ ] Missing name is rejected.
- [ ] Invalid type is rejected.
- [ ] Hierarchy cycle is rejected.
- [ ] Invalid sector/purpose reference is rejected.
- [ ] Updates preserve history.
- [ ] History can be retrieved per organization.
- [ ] Lookup/search works for other modules.
- [ ] All three base types (department, company, government structure) are supported.

## Needs Verification

- Exact status values and allowed status transitions.
- Exact identifier format rules ("where applicable").
- Exact API contracts and pagination.
- Whether sector/purpose are configurable via admin_config (doc says "if sector or purpose become configurable").
