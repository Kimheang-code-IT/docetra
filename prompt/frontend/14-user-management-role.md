# Prompt 14 — Role

## Copy/paste prompt

Implement `/user-management/roles` in the existing Nuxt UI application. Follow the shared foundation and permissions specification.

### Implement now

Add only a localized Role page header, User Management breadcrumb, administrative permission metadata, and placeholder card. Do not create permission matrices or role forms.

### Future UI contract

The finished page will manage roles and explicit permission codes. Use server-paginated role search, status and scope filters, role details, permission assignment grouped by module/action, and audit history. The permission editor must handle large permission sets with search and partial/group selection without rendering an unbounded DOM. Prevent unsafe edits to protected roles and clearly warn about affected user counts.

### Acceptance

The route is visible only through the intended navigation configuration, renders blank, and issues no request.

