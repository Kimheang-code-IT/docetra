# Prompt 01 — Dashboard

## Copy/paste prompt

Implement the Docetra Dashboard at `/` using the shared foundation, workspace components, reporting specification, and access-aware aggregate APIs.

### Page design

Build a responsive operational overview, not a raw-record page:

- Exactly **5** KPI summary cards via reusable `AppSummaryCard` (title, value, overflow menu, optional trend/deep link): active records, waiting, overdue, incoming, outgoing.
- Do **not** put a date range picker in the dashboard page header.
- “Work by stage” and “Records over time” charts: each chart header top-right uses reusable `AppChartPeriodToolbar` (year pill, period pill like Monthly, `⋯` menu with Refresh). Persist `chartYear` / `chartPeriod` in the URL.
- Full Google Calendar–style month calendar (`AppEventCalendar`) for meetings and deadlines: Today / prev-next month, day chips, selected-day agenda panel, event deep links. Do **not** show a “My work” table or Quick links block.

Do not add Kanban or a create document page to the dashboard. Aggregates must come from summary endpoints rather than downloading raw records.

### Data and states

Every KPI needs a definition, access scope, last-updated time, loading/empty/error state, and deep link carrying equivalent URL filters. Refresh related widgets together and protect against stale responses.

### Acceptance

The dashboard is responsive, filters are shareable through the URL, widgets respect permissions, charts are lazy, recent activity is cursor-paginated, and typecheck/build pass.
