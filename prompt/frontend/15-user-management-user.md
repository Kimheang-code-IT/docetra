# Prompt 15 — User

## Copy/paste prompt

Implement `/user-management/users` as a secure account-management table.

Use server search/pagination and filters for status, role, internal/external class, organization/company, linked officer, and last activity. No Kanban. Columns show name/email, linked officer, role, access class/context, status, and last sign-in without exposing credentials.

Add navigates to `/user-management/users/new`; rows navigate to `/user-management/users/:id`. The Nuxt UI document page supports account create/detail/edit, officer link, role assignment, internal/external context, enable/disable, and session/security actions. Include a right security metadata rail and immutable Security Activity for sign-in status, role/context changes, account lifecycle, and administrative actions. No casual comments.

### Acceptance

Credentials never appear, sensitive actions require confirmation, backend authorization is authoritative, and checks pass.
