# Docetra Frontend

Nuxt 4 + Vue 3 + Nuxt UI 4 application for meetings, records, organizations, users, and portal workflows.

## Stack

- Nuxt 4, Vue 3, TypeScript, Pinia, VueUse
- Nuxt UI 4 + Tailwind CSS 4
- TanStack Vue Table, ECharts, TipTap, Uppy
- English and Khmer i18n

## Architecture

```text
app/
  adapters/          # Typed entity adapters for /api/v2
  components/
    common/          # Shared filters, charts, editors, and uploaders
    document/        # Schema-driven ERP document pages
    layout/          # Application shell
    meeting/         # Reusable meeting workflows
    workspace/       # Server table and bounded Kanban kit
  composables/       # Shared page and workflow state
  config/            # Entity columns, fields, filters, and permissions
  repositories/      # Typed HTTP repositories for configuration/settings
  pages/             # Thin file-based routes
  stores/            # Pinia state
  types/             # API and domain contracts
```

Nuxt auto-imports components by folder prefix. For example, `common/AppEchart.vue` is used as `CommonAppEchart`.

## Reuse rules

| Need | Use |
|---|---|
| Entity list or Kanban | `WorkspaceEntityWorkspaceView` + `config/entities.ts` |
| Create, detail, or edit | `DocumentEntityDocumentView` |
| Meeting topic board | `MeetingAppMeetingTopicBoard` |
| Rich notes | `CommonAppRichTextNote` |
| Large uploads | `CommonAppUppyUploader` |
| Dashboard KPI/calendar | `CommonAppSummaryCard`, `CommonAppEchart`, `CommonAppEventCalendar` |

Do not add one-off page scaffolds. Extend the shared workspace, document, or meeting components.

## Mock development and API mode

- Mock mode is enabled by default with `NUXT_PUBLIC_USE_MOCK_DATA=true`.
- Development login: `admin@gmail.com` / `123456`.
- Set `NUXT_PUBLIC_USE_MOCK_DATA=false` and `NUXT_PUBLIC_API_BASE` to use the versioned `/api/v2` backend.
- Mock providers and HTTP providers implement the same typed adapter/repository contracts, so pages do not change when switching modes.
- Lists use bounded server pagination, sorting, filters, debounced search cancellation, and URL-backed state.
- API responses follow `{ data, meta, errors }`; list `meta` includes `page`, `limit`, and `total`.
- Add resources through typed adapters or repositories instead of fetching directly in page components.
- File uploads are simulated in mock mode; API mode streams them to the backend and uses server-returned metadata.

## Commands

```bash
pnpm install
pnpm dev
pnpm typecheck
pnpm build
```
