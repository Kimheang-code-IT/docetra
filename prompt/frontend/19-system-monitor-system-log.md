# Prompt 19 — System Log

## Copy/paste prompt

Implement `/system-monitor/system-logs` as a high-privilege operational log explorer.

Use a cursor-paginated server table with bounded date windows and filters for severity, environment, service/module, correlation/request ID, actor, and text search. Provide optional controlled live-tail that caps retained rows and pauses when the page is hidden.

Clicking an event navigates to `/system-monitor/system-logs/:id`, a read-only Nuxt UI event page with formatted message, timestamp, service, correlation chain, safe stack summary, metadata rail, and related events. No Kanban, comments, create, edit, or delete. Escape messages and redact credentials, tokens, personal data, request bodies, and private internals. Large export runs asynchronously.

### Acceptance

Access is restricted, live-tail is bounded, event details are safe, and checks pass.
