# Docetra Frontend

Nuxt 4 + Vue 3 + Nuxt UI 4 app for Docetra (meetings, records, organizations, users, portal).

## Stack

- Nuxt 4, Vue 3, TypeScript, Pinia, VueUse
- Nuxt UI 4 + Tailwind CSS 4
- TanStack Vue Table, ECharts, TipTap (via `UEditor`), Uppy
- i18n: English + Khmer (`i18n/locales/`)

## Folder architecture

```
app/
  adapters/          # Entity API adapters (mock ↔ /api/v2)
  components/
    common/          # Shared UI (filters, charts, rich text, uploaders)
      editor/        # TipTap helpers (resizable image node view)
    document/        # ERP document page kit
    layout/          # Shell: header, sidebar, about, user menu
    meeting/         # Meeting topic board + notes dialog
    settings/        # Settings placeholders
    workspace/       # List/Kanban workspace kit
  composables/
    layout/          # Sidebar, header, user menu
    meeting/         # Topic board logic
    workspace/       # Entity list + document page state
  config/            # Entity schemas (columns, tabs, permissions)
  layouts/           # default, auth
  middleware/        # auth.global
  mocks/             # Seed data + query helpers
  pages/             # File-based routes
  stores/            # Pinia (auth)
  types/             # Shared TS types
  utils/
    api/ auth/ constants/ editor/ filter/ role/ storage/
```

Nuxt auto-imports components by folder prefix, e.g.:

- `common/AppEchart.vue` → `CommonAppEchart`
- `meeting/AppMeetingTopicBoard.vue` → `MeetingAppMeetingTopicBoard`
- `workspace/EntityWorkspaceView.vue` → `WorkspaceEntityWorkspaceView`

## Reuse rules

| Need | Use |
|------|-----|
| Entity list / Kanban | `WorkspaceEntityWorkspaceView` + `config/entities.ts` |
| Create / detail / edit | `DocumentEntityDocumentView` |
| Meeting topic board | `MeetingAppMeetingTopicBoard` |
| Rich notes | `CommonAppRichTextNote` |
| Large uploads | `CommonAppUppyUploader` |
| Dashboard KPI / calendar | `CommonAppSummaryCard`, `CommonAppEchart`, `CommonAppEventCalendar` |

Do not add one-off page scaffolds. Prefer shared workspace/document/meeting components.

## Mock vs API

- `NUXT_PUBLIC_USE_MOCK_DATA=false` → adapters hit `runtimeConfig.public.apiBase`
- Default mock mode uses `app/mocks` + in-memory stores in `app/adapters`

## Scripts

```bash
pnpm install
pnpm dev
pnpm typecheck
pnpm build
```
