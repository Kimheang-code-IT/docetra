# Prompt 19 — System Log

## Copy/paste prompt

Implement `/system-monitor/system-logs` as a high-privilege operational log explorer.

### Navigation

Do **not** put System Log in the sidebar. Expose it from the **user menu** (`useUserMenu.ts`) as **System Log**, navigating to `/system-monitor/system-logs`. Remove any System Monitor sidebar group.

### Workspace

Use a cursor-paginated server table with bounded date windows and filters for severity, environment, service/module, correlation/request ID, actor, and text search. Provide optional controlled live-tail that caps retained rows and pauses when the page is hidden.

Per-row `⋯` (`AppRowActionsMenu`): View detail (and related safe actions only). No delete.

Clicking an event navigates to `/system-monitor/system-logs/:id`, a read-only Nuxt UI event page with formatted message, timestamp, service, correlation chain, safe stack summary, metadata rail, and related events. No Kanban, comments, create, edit, or delete. Escape messages and redact credentials, tokens, personal data, request bodies, and private internals. Large export runs asynchronously.

### Acceptance

User-menu entry works; access is restricted; live-tail is bounded; event details are safe; checks pass.
