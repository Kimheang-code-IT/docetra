# Prompt 17 — Google Drive Sync

## Copy/paste prompt

Implement `/portal/google-drive-sync` as a scaffold route using the current Nuxt UI stack and storage integration rules.

### Implement now

Render only the localized Google Drive Sync header, Portal breadcrumb, permission metadata, and placeholder. Do not connect OAuth, Google APIs, polling, or mock sync jobs.

### Future UI contract

The later UI will show configured sync sources, last and next run, current status, counts, errors, and permission-aware manual sync actions. Sync execution must be an asynchronous backend job; the browser should receive a job ID and use bounded polling or server events with cleanup. Support pagination for sync history and incremental error details. Never expose provider secrets or access tokens.

### Acceptance

The route works without external connections or network activity and the sidebar highlights it.

