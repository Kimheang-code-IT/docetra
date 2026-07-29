# Prompt 03 — Meeting History

## Copy/paste prompt

Implement the Meeting History page at `/meetings/history`. Follow the shared foundation, record history requirements, permissions specification, and existing Nuxt UI conventions.

### Implement now

Render only the localized page header, Meeting > History breadcrumb, typed route/permission metadata, and placeholder card. Do not load or fabricate history events.

### Future UI contract

The finished page will show a read-only, server-paginated meeting timeline with filters for date range, topic, meeting, status, actor, department, and action. Use cursor pagination when events can arrive while browsing. Provide expandable event details and links to permitted records. Never expose sensitive audit payloads or rely on client-side filtering of a full history dataset.

### Acceptance

The route works, no request runs during scaffold rendering, and the sidebar highlights History under Meeting.

