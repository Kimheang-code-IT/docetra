# Prompt 01 — Dashboard

## Copy/paste prompt

Implement the Docetra Dashboard route at `/` in the existing Nuxt UI application. Follow `prompt/frontend/00-shared-foundation.md` and the reporting rules in `prompt/specification/modules/reporting-support.md`.

### Implement now

Create only the blank scaffold: localized page title “Dashboard”, dashboard icon/route metadata, optional breadcrumb, and the shared placeholder card. Do not fetch data or render KPIs/charts yet.

### Future UI contract

Later this page will provide access-aware operational summaries for records, documents, meetings, organizations, storage activity, and workflow status. It should use compact KPI cards, time/organization/status filters, and lazy-loaded ECharts panels backed by aggregate endpoints. Never calculate enterprise-wide metrics by downloading raw records. Every metric must have a clear definition, loading/empty/error state, last-updated value, and permission-aware scope.

### Acceptance

The `/` route renders in the authenticated shared layout, Dashboard is active in the sidebar, no API request is made, and typecheck/build remain clean.

