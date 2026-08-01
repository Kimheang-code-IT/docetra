# Prompt 18 — Portal Logs

## Copy/paste prompt

Implement `/portal/logs` as a read-only upload and synchronization activity explorer titled **Logs**.

Use a cursor-paginated `AppServerTable` (or thin `EntityWorkspaceView`) with operation type, source, status, actor, file, job ID, date, and retryable filters. Columns use dynamic badge/datetime cell logic where appropriate.

Rows support:

- Row click → `/portal/logs/:id`
- Per-row `⋯` (`AppRowActionsMenu`): View detail · View logs (and Retry only when the job is explicitly retryable and the user has permission)

Detail page `/portal/logs/:id` is a read-only Nuxt UI event page with safe details, related file/job, error summary, metadata rail, and activity chain.

Do not add Kanban, create/edit forms, or comments. Redact storage credentials, provider tokens, signed URLs, and unsafe request payloads.

### Acceptance

Title is **Logs**; logs are immutable; retries are controlled; details are redacted; row actions work; checks pass.
