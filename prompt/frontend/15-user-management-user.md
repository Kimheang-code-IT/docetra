# Prompt 15 — User

## Copy/paste prompt

Implement the User page at `/user-management/users` using the existing Nuxt UI frontend and people/access rules.

### Implement now

Create only the localized User header, User Management breadcrumb, administrative route/permission metadata, and placeholder. Do not implement account creation, password controls, or a table.

### Future UI contract

The full page will manage authentication accounts, linked officer, assigned role(s), internal/external access class, organization/company context, status, and last activity where permitted. Use server-side pagination/search/filtering. Never display credential material. Account enable/disable, role changes, officer links, and external context changes require confirmation, backend enforcement, and audit history.

### Acceptance

The page route and sidebar active state work with no business data or API activity.

