# Prompt 17 — Google Drive Sync (remaining)

> **Status:** Partial — list/detail shell exists via generic `EntityWorkspaceView`. Dedicated sync UI below is still open.

## Current code

| Piece | Location |
| --- | --- |
| List | `frontend/app/pages/portal/google-drive-sync/index.vue` |
| Create / detail | `…/new.vue`, `…/[id].vue` |
| Entity config | `config/entities.ts` → `googleDriveSync` |
| Adapter | `adapters/createEntityAdapter` mock/HTTP entity adapter |
| Nav | Sidebar Portal → Google Drive Sync (`useMenu.ts`) |

Today the page is a standard entity workspace (table + document page), not the sync-source / job console described below.

## Remaining work

Replace the generic workspace with a sync-source + job workspace:

- Source **status cards** + server-paginated **job table** (no Kanban).
- Show connection state, folder/source, last/next run, current job, imported/skipped/failed counts, error summary.
- Filters: source, status, trigger, actor, date (`AppDateRangeFilter` / `AppFilterSelect` patterns).
- Source Add → `/portal/google-drive-sync/sources/new`.
- Source and job rows → their detail routes.
- Detail tabs: Configuration, Recent Files, Errors, immutable Activity (`AppDocumentPage` stack).
- Manual Sync creates an async job with bounded polling (or server events) and cleanup.
- Never expose provider secrets or access tokens (`AppSecretInput` only for editable secrets).
- Keep row actions via `AppRowActionsMenu` where applicable; Logs deep-link to `/records/record-logs` or portal logs as product decides.

Reuse existing shell patterns from File Upload / Settings connection cards before inventing new chrome. Prefer thin pages + a dedicated composable (e.g. `useGoogleDriveSync`) and repository behind `useMockData`.

## Acceptance

Long-running jobs do not block the browser, status refresh is bounded, secrets stay protected, and typecheck/build pass.
