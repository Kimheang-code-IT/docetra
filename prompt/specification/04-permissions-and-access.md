# Docetra v2 Permissions and Access

## Purpose

This document defines the access-control model for Docetra v2. It describes how users, roles, departments, organizations, and external company access should work in the system.

## Access model summary

Docetra v2 uses a role- and context-aware access model. Access decisions depend on:
- the authenticated user.
- the linked officer, if any.
- the user’s role.
- the user’s organization or department.
- the record’s owning or related organizational context.
- whether the user is internal or external.

Backend enforcement is mandatory for all access decisions.

## Access principles

- Permissions must never be assumed from the UI.
- Access must be checked on every protected request.
- External access must be restricted to explicitly shared data.
- Internal access must respect department and role scope.
- Sensitive operations must be auditable.

## Identity model

### User account
A user account is the authentication identity used to sign in.

### Officer
An officer is the business person entity. A user account may be linked to an officer, but not every officer needs a user account.

### Identity mapping rule
The system must preserve the possibility that an officer exists without login access.

## Access categories

### Internal users
Internal users are officers and staff who operate inside the organization’s departments or teams.

### External users
External users are company representatives who may access only the records and resources explicitly shared with their company context.

## Role model

Roles are used to group permissions. A role may represent a job function, department function, or access class.

Examples of role-driven capabilities:
- view records.
- create records.
- update records.
- archive and restore owned records where allowed.
- soft-delete records where allowed; this is recoverable only by an administrator.
- manage configuration.
- manage users and permissions.
- access reports.
- manage external sharing.

## Permission model

Permissions should be represented as explicit capabilities, not inferred behavior.

Permissions should be assignable to roles for:
- navigation visibility.
- create actions.
- edit actions.
- archive, restore, soft-delete, and administrator-purge actions.
- view actions.
- approve or finalize actions if introduced later.
- configuration actions.
- export actions.
- administrative actions.

## Department-aware access

Many access checks depend on both role and organizational scope.

The system must support:
- department ownership.
- department-based visibility.
- cross-department collaboration where allowed.
- management-level broader access where permitted by role.

## Record visibility rules

A user may view a record only if the backend determines the user has access based on the record’s visibility rules.

A record may be visible because:
- the user owns it.
- the user belongs to the owning department.
- the user has a role that grants broader access.
- the record is shared with the user’s company or organization.
- the user is part of a permitted review or collaboration group.

## Sharing rules

Shared records must be explicitly governed.

Sharing must support:
- internal sharing across departments.
- external sharing with companies.
- controlled visibility for shared records.
- explicit relationship to the target organization or company.

The system must avoid accidental overexposure of data.

## Action-level access

The following actions should be independently controlled:
- view.
- create.
- edit.
- archive.
- restore.
- delete.
- purge (administrator-only and never creator-scoped).
- assign.
- share.
- export.
- configure.
- manage access.
- review or finalize if a workflow requires it.

Lifecycle authorization is status-aware. An owner may restore their own archived record, but cannot read or restore a soft-deleted tombstone. An administrator with `.restore` may recover a tombstone. `.purge` permanently removes eligible data only after retention, legal-hold, dependency, and last-administrator safeguards; it must never be granted through creator-only scope. Shared Role definitions are administrator-managed configuration, while a user's self-delete request disables their account and revokes all sessions.

## Administrative access

Administrative access should be reserved for roles that manage system configuration, permissions, record definitions, or global settings.

Examples:
- record type management.
- record attribute management.
- document type management.
- setting management.
- user and role management.
- audit log review.

## Audit and traceability

Access-related actions should be logged when they are significant, especially:
- permission changes.
- role assignment changes.
- sharing changes.
- external access changes.
- configuration changes affecting visibility.
- archive, restore, soft-delete, purge, comment, and account-disable actions.

## External access model

External company users must be limited to:
- records shared with their company.
- resources explicitly exposed to their company context.
- actions allowed by their assigned permissions.

External users must not gain implicit access to internal-only records or private organizational data.

## Permission evaluation order

The backend should evaluate access in a predictable order:
1. Authenticate the user.
2. Resolve the linked officer or user context.
3. Determine internal or external access class.
4. Check role permissions.
5. Check organizational scope.
6. Check record sharing context.
7. Grant or deny access.

## Implementation notes

- Access checks should be centralized in reusable backend services.
- Permission logic should not be duplicated across controllers.
- Sensitive endpoints should use explicit authorization gates.
- Access rules should be testable through integration and contract tests.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `02-domain-model.md`
- `03-functional-requirements.md`
- `05-user-flows.md`
- `06-api-contracts.md`
- `07-data-model.md`
- `modules/people-access.md`
