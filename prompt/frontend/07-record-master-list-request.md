# Prompt 07 — Master List Request

## Copy/paste prompt

Implement `/records/master-list-requests` as a configuration-driven workflow workspace.

### Page design

Use table and Kanban views with search and filters for requester, owner organization/department, request date, status, stage, waiting state, assignee, and due date. Rows/cards show request number, title, requester, owner, date, due state, assignee, and current stage.

Add navigates to `/records/master-list-requests/new`; rows and cards navigate to `/records/master-list-requests/:id`. The Nuxt UI document page renders configured attributes, related records, generated/attached files, a metadata rail, and access controls. Place Comments & Activity below the form. Activity tracks assignment, workflow, field changes, file generation, comments, and notifications.

Do not hardcode variable business fields; obtain them from record type/template metadata.

### Acceptance

Dynamic fields render safely, both views share server state, overdue indicators are accessible, document-page collaboration works, and checks pass.
