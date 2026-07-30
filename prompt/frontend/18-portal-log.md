# Prompt 18 — Portal Log

## Copy/paste prompt

Implement `/portal/logs` as a read-only upload and synchronization activity explorer.

Use a cursor-paginated server table with operation type, source, status, actor, file, job ID, date, and retryable filters. Rows navigate to `/portal/logs/:id`, a read-only Nuxt UI event page with safe details, related file/job, error summary, metadata rail, and activity chain. Provide Retry only for explicitly retryable failed jobs and only with permission.

Do not add Kanban, create/edit forms, or comments. Redact storage credentials, provider tokens, signed URLs, and unsafe request payloads.

### Acceptance

Logs are immutable, retries are controlled, details are redacted, and checks pass.
