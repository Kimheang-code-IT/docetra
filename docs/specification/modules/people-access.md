# Docetra v2 Module: People and Access

## Purpose

The people and access module manages officers, user identity mapping, roles, permissions, and access-control behavior in Docetra v2. It is responsible for ensuring that the right users can access the right data for the right organizational context.

## Module responsibilities

The people and access module owns:
- officer records.
- user account mapping.
- role definitions.
- permission definitions.
- role-permission assignments.
- menu or action access codes.
- internal access rules.
- external access context.
- identity resolution for authenticated users.

## Core concepts

### Officer
An officer is the business-side person entity. Officers represent internal people who may operate in the system.

### User account
A user account is the authentication identity used to sign in.

### Role
A role groups permissions and defines an access profile for a user or officer.

### Permission
A permission is a specific capability or access right in the system.

### Access context
Access context is the combination of user identity, role, department, organization, and internal or external status used to determine what a user can do.

## Functional behavior

### Officer management
The module must support creating, updating, and looking up officer records.

### User mapping
The module must support linking a user account to an officer when applicable.

### Role management
The module must support defining and maintaining roles.

### Permission management
The module must support defining permissions and assigning them to roles.

### Access evaluation
The module must support access checks for internal and external users.

### Menu or action access
The module must support permission control for navigation items and action codes where needed.

## Identity rules

- Not every officer needs a user account.
- A user account should map to one officer where required.
- Access must not depend solely on frontend state.
- Backend authorization must be the source of truth.

## Access behavior

### Internal access
Internal users should access data based on role and organizational scope.

### External access
External users should only access data explicitly shared with their company or permitted context.

### Permission evaluation
The module should provide reusable permission checks for other modules and API handlers.

## Data ownership

The people and access module should own or primarily manage:
- `officer`
- `users`
- `role`
- `permission`
- `role_permission`
- `menu`

If additional access tables are introduced later, they should remain under this module unless explicitly reassigned.

## Key validations

The module should validate:
- officer identity uniqueness where required.
- user-to-officer mapping consistency.
- role definitions are valid.
- permission assignments reference valid permission codes.
- access rules are consistent with internal and external context.

## API responsibilities

The module should expose APIs for:
- officer list and detail.
- officer create and update.
- user-officer mapping.
- role list and detail.
- role create and update.
- permission assignment and lookup.
- access validation and scope lookup where needed.

## Dependency boundaries

The module may depend on:
- organization for department or company context.
- record for record-specific access checks.
- admin_config for system-level settings if access rules become configurable.

The module should not own business workflows outside of access control and identity management.

## Implementation notes

- Keep access logic centralized and reusable.
- Use explicit permission codes.
- Support both internal and external access from the beginning.
- Preserve the ability for officers to exist without login accounts.
- Avoid duplicating access rules in controllers or UI code.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `02-domain-model.md`
- `03-functional-requirements.md`
- `04-permissions-and-access.md`
- `07-data-model.md`
- `modules/organization.md`
- `modules/record.md`
