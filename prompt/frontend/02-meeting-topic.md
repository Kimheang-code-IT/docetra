# Prompt 02 — Meeting Topic

## Copy/paste prompt

Implement the Meeting Topic page at `/meetings/topics` using the existing Nuxt 4 + Nuxt UI 4 stack. Follow the shared foundation and the record module specification.

### Implement now

Create only a localized header, Meeting > Topic breadcrumb, route/permission metadata, and the standard placeholder card. Do not create a board, drag-and-drop, table, form, mock data, or API call.

### Future UI contract

This page will manage meeting-topic records and their child meetings. It must support server-filtered topic discovery, topic status/stage, vertical ordered child meetings, and the rule that linking a meeting into a topic removes it from the standalone meeting collection. Future drag-and-drop must be keyboard accessible, optimistic only with rollback, conflict-safe, and confirmed by the backend. Large topic collections must be paginated or incrementally loaded.

### Acceptance

The route is reachable from Meeting > Topic, active navigation is correct, the scaffold has no business data, and checks pass.

