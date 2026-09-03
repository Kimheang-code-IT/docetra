# Frontend

Stack: Nuxt 4, Vue 3, TypeScript, Nuxt UI 4, Tailwind 4, Pinia, i18n `en`/`km`. Layout map: `prompt/frontend/`. Shared foundation: `prompt/frontend/00-shared-foundation.md`.

## Layout

```
frontend/app/
  adapters/       # only $fetch boundary (plus repositories)
  components/     # common, document, layout, meeting, workspace, configuration, settings
  composables/
  config/entities.ts
  pages/          # thin routes
  stores/
  types/docetra/
```

Nuxt prefixes components by folder: `common/AppEchart.vue` → `CommonAppEchart`.

## Reuse (mandatory)

| Need | Use |
| --- | --- |
| Entity list / table / Kanban | `WorkspaceEntityWorkspaceView` + `config/entities.ts` |
| Create / show / edit | `DocumentEntityDocumentView` + `useDocumentPage` |
| Meeting topic / record stage / record log boards | `WorkspaceAppBoardShell` + `WorkspaceAppBoardRailItem` / `RailPill` + `WorkspaceAppBoardContent` (cards/table toggle) |
| Board card (records + meetings) | `RecordAppRecordBoardCard` (`meeting` prop enables meeting mode) |
| Record stage board | `RecordAppRecordStageBoard` |
| Meeting topic board | `MeetingAppMeetingTopicBoard` |
| Uploads | `CommonAppUppyUploader` |
| HTTP | `useApi()` via adapters / repositories |

Do not add one-off list or document page scaffolds.

## API

- Cookie session by default (`NUXT_PUBLIC_AUTH_MODE=cookie`). Empty `NUXT_PUBLIC_API_BASE` = same-origin `/api/v2` proxied to FastAPI.
- Paths live in `frontend/app/utils/constants/api-endpoints.ts`. Dynamic records: `ApiEndpoints.RECORDS(typeCode)`.
- Shared CRUD: `frontend/app/adapters/createEntityAdapter.ts`.
- CSRF on mutating requests. Same-origin URL check in `useApi`.
- Concurrency: `version` body + `If-Match` via `frontend/app/utils/api/concurrency.ts`.

## UI conventions

- User-facing strings: i18n keys in `en.json` and `km.json`. No hardcoded labels in pages.
- Form controls: Nuxt UI `variant: soft` unless a control is a deliberate exception.
- List shell padding: `px-1.5 pt-1.5 pb-0`. Document show/create: `p-0`.
- Page permission in `definePageMeta({ permission: '…' })`. Denials use the global access dialog, not a dedicated 403 page.
- `AuthUser.permissions` is authoritative in the UI when present; `pageAccess` is legacy.

## Routing / remount

`app.vue` page key is `route.path` (not `fullPath`) so query changes (filters, sort, page) do not destroy the view. Path changes still remount list vs `/new` vs `/{id}`.

## Verify

From `frontend/`: `pnpm test:unit`, `pnpm typecheck`. If the change is user-visible, exercise the route in the browser (not only a screenshot).
