# Prompt 08 — Record Log

## Copy/paste prompt

Implement `/records/logs` as a read-only record audit explorer.

### Page design

Use `AppServerTable` with cursor pagination. Filters include record ID/title, record type, action, actor, organization, date range, correlation ID, and severity/category. Columns show event time, record, type, action, actor, organization, and compact summary.

Navigate to `/records/logs/:id` for a read-only Nuxt UI event page containing event summary, safe before/after changes, request/correlation context, linked record, metadata rail, and related activity. Do not include Kanban, Add, Edit, Delete, or comment composition.

Escape event content and redact private fields, tokens, storage URLs, and backend-only payloads.

### Acceptance

Events are immutable, filters remain shareable, the event page is permission-aware and redacted, and checks pass.
