# Prompt 17 — Google Drive Sync

## Copy/paste prompt

Implement `/portal/google-drive-sync` as a sync-source and job workspace.

Use source status cards plus a server-paginated job table; do not use Kanban. Show connection state, folder/source, last/next run, current job, imported/skipped/failed counts, and error summary. Filters: source, status, trigger, actor, and date.

Source Add navigates to `/portal/google-drive-sync/sources/new`; source and job rows navigate to their canonical detail routes. Use Nuxt UI document pages for permitted source configuration and read-only job details. Tabs include Configuration, Recent Files, Errors, and immutable Activity. Manual Sync creates an asynchronous backend job and uses bounded polling or server events with cleanup. Never expose provider secrets or access tokens.

### Acceptance

Long-running jobs do not block the browser, status refresh is bounded, secrets are protected, and checks pass.
