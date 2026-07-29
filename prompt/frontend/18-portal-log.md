# Prompt 18 — Portal Log

## Copy/paste prompt

Implement the Portal Log page at `/portal/logs`, following the shared foundation and storage integration module.

### Implement now

Create only the localized Portal > Log header/breadcrumb, permission metadata, and blank placeholder card. Do not load upload or sync events.

### Future UI contract

The finished page will show server-paginated upload and synchronization activity with filters for operation type, source, status, actor, file, job ID, and date range. Use cursor pagination for append-heavy logs and lazy-load detailed errors. Redact storage credentials, provider tokens, private URLs, and unsafe request payloads. Provide retry only for explicitly retryable failed jobs.

### Acceptance

The blank page loads through Portal navigation and makes no API request.

