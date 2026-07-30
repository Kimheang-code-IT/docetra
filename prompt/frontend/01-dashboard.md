# Prompt 01 — Dashboard

## Copy/paste prompt

Implement the Docetra Dashboard at `/` using the shared foundation, workspace components, reporting specification, and access-aware aggregate APIs.

### Page design

Build a responsive operational overview, not a raw-record page:

- KPI cards: active records, waiting records, overdue work, meetings, incoming documents, outgoing documents, and recent uploads.
- Global date range, organization, record type, status, and stage filters.
- “Work by stage” chart and “Records over time” chart using lazy-loaded ECharts.
- Compact “My work” table linking to permitted records.
- Recent Activity panel using the read-only timeline portion of `AppCommentsActivity`.
- Quick links to the main record workspaces.

Do not add Kanban or a create document page to the dashboard. Aggregates must come from summary endpoints rather than downloading raw records.

### Data and states

Every KPI needs a definition, access scope, last-updated time, loading/empty/error state, and deep link carrying equivalent URL filters. Refresh related widgets together and protect against stale responses.

### Acceptance

The dashboard is responsive, filters are shareable through the URL, widgets respect permissions, charts are lazy, recent activity is cursor-paginated, and typecheck/build pass.
