# Prompt 17 — Google Drive Sync (remaining)

> **Status:** Partial — list/detail shell exists via generic `EntityWorkspaceView`. Dedicated sync UI below is still open.

## Current code

| Piece | Location |
| --- | --- |
| List | `frontend/app/pages/portal/google-drive-sync/index.vue` |
| Create / detail | `…/new.vue`, `…/[id].vue` |
| Entity config | `config/entities` → `googleDriveSync` |
| Adapter | `adapters` mock entity adapter |

## Remaining work

Replace the generic workspace with a sync-source + job workspace:

- Source **status cards** + server-paginated **job table** (no Kanban).
- Show connection state, folder/source, last/next run, current job, imported/skipped/failed counts, error summary.
- Filters: source, status, trigger, actor, date.
- Source Add → `/portal/google-drive-sync/sources/new`.
- Source and job rows → their detail routes.
- Detail tabs: Configuration, Recent Files, Errors, immutable Activity.
- Manual Sync creates an async job with bounded polling (or server events) and cleanup.
- Never expose provider secrets or access tokens.

## Acceptance

Long-running jobs do not block the browser, status refresh is bounded, secrets stay protected, and typecheck/build pass.
