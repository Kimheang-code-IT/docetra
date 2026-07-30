# Prompt 04 — Incoming Document

## Copy/paste prompt

Implement `/records/incoming-documents` as a complete workflow workspace using the shared table, Kanban, ERP-style document page, dynamic fields, attachments, comments, and activity components.

### Views

- Table and stage-based Kanban toggle.
- Search plus filters for received date, sender organization, owner department, document type, status, stage, waiting state, assignee, and attachment presence.
- Rows/cards show reference number, title, sender, received date, owner, assignee, stage, waiting state, and attachment/comment counts.
- Stage movement must use validated transitions with rollback.

### Create and document pages

Add navigates to `/records/incoming-documents/new`; rows and cards navigate to `/records/incoming-documents/:id`. The Nuxt UI document page captures reference, title, sender, received date, owner, type, stage, and files. Tabs contain Details, Organizations, Relationships, Files, and Access; the right rail contains assignment, tags, sharing, and ownership. Place Comments & Activity below the form. Activity records creation, edits, assignment, workflow, sharing, attachments, comments, and emails. Provide “New Email” only when permitted.

### Acceptance

Both views use server data and shared URL state, the document form is schema-driven, activity is immutable, comments are writable, and checks pass.
