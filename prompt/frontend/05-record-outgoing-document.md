# Prompt 05 — Outgoing Document

## Copy/paste prompt

Implement `/records/outgoing-documents` using the reusable workflow workspace.

### Views

Provide table and stage-based Kanban. Filters include sent/planned date, recipient organization, owner department, document type, status, stage, waiting state, assignee, delivery channel, and attachment presence. Cards/rows show reference, title, recipient, date, owner, stage, waiting state, and attachment/comment counts.

### Create and document pages

Add navigates to `/records/outgoing-documents/new`; rows and cards navigate to `/records/outgoing-documents/:id`. Use the shared Nuxt UI document shell with Details, Recipients, Relationships, Files, Delivery, and Access tabs; assignment, tags, sharing, and ownership live in the right rail. Place Comments & Activity below the form. Add permission-aware send/share/export actions. Activity shows creation, edits, dispatch events, workflow changes, recipients, attachments, sharing, and emails.

Bulk actions must use explicit IDs or a server-side selection token. Stage changes require backend validation and rollback.

### Acceptance

Table/Kanban state is URL-backed, recipient and workflow behavior are distinct from incoming documents, the document page is reusable, and checks pass.
