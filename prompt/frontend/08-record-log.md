# Prompt 08 — Record Log

## Copy/paste prompt

Implement the Record Log page at `/records/logs`. Use the shared foundation and Docetra auditability requirements.

### Implement now

Render only a localized page header, Record > Log breadcrumb, permission metadata, and blank placeholder. Do not load audit data.

### Future UI contract

Build this later as a read-only, server-paginated operational history for record changes. Filters should include record ID/type, action, actor, organization, date range, and request/correlation ID. Prefer cursor pagination for append-heavy logs. Event payloads should be summarized by default, expandable on demand, safely redacted, and linked to records only when the user has permission.

### Acceptance

The scaffold makes no request and the Log link is correctly highlighted in the Record group.

