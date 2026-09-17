# docetra-people-access

## Purpose

Use when implementing or modifying officers, user accounts, roles, permissions, role-permission assignments, menu/action access, or any authorization logic in Docetra.

## Source Documents

- docs/specification/modules/people-access.md

## Domain Overview

The people and access module ensures the right users can access the right data for the right organizational context. It owns identity (officers + user accounts) and access control (roles, permissions, menus, internal/external access) and provides reusable permission checks for all other modules. It must not own business workflows outside access control and identity management.

## Key Entities

| Entity | Responsibility |
|---|---|
| Officer | Business-side person entity; internal people who may operate in the system |
| User account | Authentication identity used to sign in |
| Role | Groups permissions; defines an access profile for a user or officer |
| Permission | A specific capability or access right |
| Access context | User identity + role + department + organization + internal/external status, used to determine what a user can do |
| Menu | Navigation items / action access codes under permission control |

## Relationships

- User account → Officer (mapping when applicable).
- Role → Permissions (role_permission assignments).
- User/Officer → Role (access profile).
- Access context may reference organization/department (module may depend on organization for context).

## Business Rules

- Not every officer needs a user account — officers MUST be able to exist without login accounts.
- A user account SHOULD map to one officer where required (one-to-one consistency).
- Access MUST NOT depend solely on frontend state.
- Backend authorization MUST be the source of truth.
- Internal users access data based on role and organizational scope.
- External users access ONLY data explicitly shared with their company or permitted context.
- Permission checks MUST be centralized and reusable — never duplicated in controllers or UI code.
- Permission codes MUST be explicit.
- Both internal and external access MUST be supported from the beginning.

## Permissions

This module DEFINES permissions. Exact permission codes and the role matrix: `Needs verification` (04-permissions-and-access.md was not provided).

- The module must support permission control for navigation items (menus) and action codes.
- It must provide access evaluation for internal and external users.

## Implemented Behavior (verified in code)

- **Officers**: `/officers` (+ new/[id]), permission `organizations.officers.view`. Officers attach as **participants** to meetings and documents via officer @mention selects (`participants`, `involvedOfficers`).
- **Users**: `/user-management/users` (+ new/[id]); user form maps to an officer via `officerId` select.
- **Roles**: `/user-management/roles` (+ new/[id]); dynamic permission catalog (`repositories/contracts/permission-catalog.ts`).
- Frontend permission gating (`auth.canAccessPage(config.permission)`) is UX only; backend authorization is authoritative.

## API Rules

The module SHOULD expose APIs for:

- Officer: list, detail, create, update.
- User–officer mapping.
- Role: list, detail, create, update.
- Permission: assignment and lookup.
- Access validation and scope lookup where needed.

Exact routes/payloads: `Needs verification`.

## Data Rules

Module owns or primarily manages: `officer`, `users`, `role`, `permission`, `role_permission`, `menu`.

- Additional access tables introduced later remain under this module unless explicitly reassigned.

## Validation Rules

- Officer identity uniqueness where required.
- User-to-officer mapping consistency (one user ↔ one officer where required).
- Role definitions are valid.
- Permission assignments reference valid permission codes.
- Access rules are consistent with internal/external context.

## Edge Cases

- Officer with no user account → must still be a valid, manageable record. (Explicit in spec.)
- External user attempting to access data not shared with their company → must be denied. (Derived from specification: external users only access explicitly shared data.)
- Officer belonging to multiple organizational scopes. `Needs verification` — doc does not define this.

## Implementation Guidance

- Keep access logic centralized and reusable (services other modules call).
- Use explicit permission codes everywhere.
- Never implement authorization checks inside frontend-only logic; frontend state is presentation only.
- Do not duplicate access rules in controllers or UI code.

## DO NOT

- DO NOT make access depend solely on frontend state.
- DO NOT force every officer to have a user account.
- DO NOT let external users see data not explicitly shared with their company/permitted context.
- DO NOT own business workflows in this module.
- DO NOT duplicate permission checks across controllers/UI.

## Testing Checklist

- [ ] Officer can be created without a user account.
- [ ] User account maps to one officer consistently.
- [ ] Roles can be created/updated with valid permission codes.
- [ ] Invalid permission code assignment is rejected.
- [ ] Internal user access respects role + organizational scope.
- [ ] External user cannot access unshared data.
- [ ] Backend authorization denies what frontend hides but doesn't permit.
- [ ] Permission checks are reusable from other modules (centralized service).

## Needs Verification

- Exact permission codes and role catalog.
- Exact API contracts.
- Relationship between menu entries and permission codes.
- Whether a user account may map to more than one officer (doc says "should map to one officer where required" — one-to-one assumed, derived from specification).
