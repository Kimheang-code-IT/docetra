# Prompt 03 — Meeting History

## Copy/paste prompt

Implement the read-only Meeting History workspace at `/meetings/history`.

### Page design

Use `AppServerTable` with an optional timeline-view toggle, not Kanban. Filter by date range, meeting/topic, status, stage, actor, department, organization, and action. Columns include record time, meeting, topic, action, previous/new state summary, actor, and organization.

Clicking a row navigates to `/meetings/history/:id`, a read-only Nuxt UI event page with a sticky header, event summary, safe before/after changes, linked meeting/topic, permitted attachments, correlation ID, metadata rail, and activity timeline. Do not show a comment composer or create/edit actions.

Use cursor pagination because history can grow while the user is browsing. Redact sensitive metadata and deep-link only to records the user can view.

### Acceptance

History remains immutable, filters are URL-backed, event details are safe and permission-aware, and checks pass.
