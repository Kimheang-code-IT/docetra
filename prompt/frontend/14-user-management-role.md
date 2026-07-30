# Prompt 14 — Role

## Copy/paste prompt

Implement `/user-management/roles` using the shared table and Nuxt UI document-page system.

Use a server table with search, status, scope, protected-role, permission-count, and user-count filters. No Kanban. Add navigates to `/user-management/roles/new`; rows navigate to `/user-management/roles/:id`. The document page contains role identity and a scalable permission editor grouped by module and action, with search, indeterminate group selection, navigation visibility, affected-user summary, metadata rail, and Security Activity.

Include immutable security Activity for role creation, permission changes, assignments, status, and protected-role actions. Do not include casual comments. Confirm high-impact changes and prevent unsafe edits to protected roles.

### Acceptance

Large permission sets remain performant and accessible, permission changes are auditable, and checks pass.
