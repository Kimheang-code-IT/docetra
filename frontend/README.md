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

## API mode

The UI always calls FastAPI. There is no in-browser mock dataset.

```env
NUXT_PUBLIC_USE_MOCK_DATA=false
NUXT_PUBLIC_AUTH_MODE=cookie
NUXT_PUBLIC_API_BASE=http://localhost:8000
```

1. Start the backend: `docker compose --env-file backend.env -f compose.backend.yml up --build -d`
2. Start Nuxt: `pnpm dev` (port 3000; CORS already allows this origin)
3. Sign in with `admin@gmail.com` / `123456` (HttpOnly JWT cookies; no token in JSON)

Lists use bounded server pagination. Adapters/repositories are the only `$fetch` boundary. Uploads go to `/api/v2/portal/file-uploads` with cookies + CSRF.

## Commands

```bash
pnpm install
pnpm dev
pnpm typecheck
pnpm build
```
