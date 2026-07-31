# Prompt 14 — Role

## Copy/paste prompt

Implement `/user-management/roles` using the shared table and Nuxt UI document-page system.

Use a server table with columns **Role name**, **Users**, **Permissions**, **Status**. Filters: search, status. No Kanban. Add navigates to `/user-management/roles/new`; rows navigate to `/user-management/roles/:id`.

### New / edit Role page

ERPNext-style permission matrix (`AppRolePermissionMatrix`):

- Role identity fields: code, role name, status, description.
- Permissions table lists **all document types** automatically (no add-row / remove icons).
- Columns: Document Type, Permissions checkbox grid only (no Role / Level columns — role identity is already on the form).
- Persist `permissionRows` on the role; derive `permissionCount` / flat `permissions` on save.
- No section subtitle under Role permissions. Security Activity for role creation and permission changes.

### Acceptance

Large permission sets remain performant and accessible, permission changes are auditable, and checks pass.
