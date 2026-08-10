# Docetra Frontend Prompts

Architecture references for the Docetra v2 UI in `frontend/`. Align product presentation with `prompt/idea/` and `prompt/specification/`; this folder only describes how the current Nuxt app is built.

## Status

Most page prompts are **removed** — those routes already have working UI and logic (mock adapters / repositories).

| Area | Status |
| --- | --- |
| Shared shell, workspace kit, config/settings kit | Done — see `00-*.md` as architecture reference |
| Pages `01`–`16`, `18`–`28` | Done — prompts deleted |
| Google Drive Sync (`17`) | **Partial** — remaining prompt kept |

## Remaining page work

| # | Page | Route | Prompt |
| --- | --- | --- | --- |
| 17 | Google Drive Sync | `/portal/google-drive-sync` | [`17-portal-google-drive-sync.md`](./17-portal-google-drive-sync.md) |

## Architecture references (implemented)

Keep these as “how the app is built” docs, not copy/paste build tickets:

| File | Role |
| --- | --- |
| [`00-product-ui-design-map.md`](./00-product-ui-design-map.md) | Product UI patterns |
| [`00-reusable-workspace-components.md`](./00-reusable-workspace-components.md) | Tables, Kanban, document pages, boards |
| [`00-shared-foundation.md`](./00-shared-foundation.md) | Shell, nav, i18n, padding, loading, search |
| [`00B-configuration-settings-kit.md`](./00B-configuration-settings-kit.md) | Configuration & Settings schemas / editors |

Developer inventory (code-side): `frontend/docs/reusable-components-guide.md`.

## Implemented route inventory

| Nav | Page | Route | Main implementation |
| --- | --- | --- | --- |
| — | Dashboard | `/` | `pages/index.vue` |
| Meeting | Topic | `/meetings/topics` | `AppMeetingTopicBoard` + `useMeetingTopicBoard` |
| Meeting | History | `/meetings/history` | `EntityWorkspaceView` |
| Record | Incoming Document | `/records/incoming-documents` | `AppRecordStageBoard` + `useRecordStageBoard` |
| Record | Outgoing Document | `/records/outgoing-documents` | `AppRecordStageBoard` |
| Record | Document | `/records/documents` | `AppRecordStageBoard` |
| Record | Master List Request | `/records/master-list-requests` | `AppRecordStageBoard` |
| Record | Logs | `/records/record-logs` | `AppRecordLogBoard` + `useRecordLogBoard` |
| Organization | Department | `/organizations/departments` | `EntityWorkspaceView` |
| Organization | Company | `/organizations/companies` | `EntityWorkspaceView` |
| Organization | Company Purpose | `/organizations/company-purposes` | `EntityWorkspaceView` |
| Organization | Company Sector | `/organizations/company-sectors` | `EntityWorkspaceView` |
| Organization | Officer | `/organizations/officers` | `EntityWorkspaceView` |
| User Management | Role | `/user-management/roles` | `EntityWorkspaceView` + `AppRolePermissionMatrix` |
| User Management | User | `/user-management/users` | `EntityWorkspaceView` |
| Portal | File Upload | `/portal/file-upload` | `AppFileUploadBoard` |
| Portal | Google Drive Sync | `/portal/google-drive-sync` | Partial — generic `EntityWorkspaceView` |
| Portal | Logs | `/portal/portal-logs` | `EntityWorkspaceView` (read-only) |
| User menu | System Log | `/system-monitor/system-logs` | `EntityWorkspaceView` (read-only) |
| Auth | Login | `/auth/login` | Auth forms (`/login` redirects here) |
| Auth | Forget Password | `/auth/forget-password` | Auth forms (`/forget-password` redirects) |
| Auth | Verify / Reset | `/auth/verify-code`, `/auth/reset-password` | Auth forms |
| Configuration | Record Type | `/configuration/record-types` | `AppRecordTypeList` / `AppRecordTypeEditor` |
| Configuration | Record Attribute | `/configuration/record-attributes` | `AppRecordAttributeList` / `AppRecordAttributeEditor` |
| Settings | App Info | `/settings/app-info` | `AppDocumentPage` + settings repos |
| Settings | App Config | `/settings/app-config` | `AppDocumentPage` + display **card fields** editor |
| Settings | Storage | `/settings/storage` | Settings storage UI |

Shared confirmations: `useConfirm()` + `CommonAppConfirmHost` in `app.vue`.

## Current product behaviors (code)

- **Entity config hub:** `app/config/entities.ts` drives most CRUD list/detail pages via `EntityWorkspaceView` / `EntityDocumentView`.
- **Record documents** (incoming / outgoing / document / master list): tabs/fields merge from selected record type via `useRecordTypeDrivenTabs`.
- **Board cards** (meeting + record): visible slots / footer align come from App Config display → `useCardFields` + `AppCardFieldsEditor`.
- **Cmd+K global search:** `layouts/default.vue` + `useGlobalSearch` (keyword / semantic; Ask AI on demand). Page toolbars keep local `AppLiveSearch`.
- **User preferences:** locale + font size (`stores/preferences.ts`); appearance via color mode; System Log / About / Logout from `useUserMenu`.
- **Data mode:** `runtimeConfig.public.useMockData` (default true) switches repositories between mock localStorage and HTTP.

## Technology baseline

Align with `frontend/package.json` (do not invent newer majors):

| Package | Version |
| --- | --- |
| `nuxt` | `^4.3.1` |
| `vue` | `^3.5.29` |
| `@nuxt/ui` | `^4.5.1` |
| `pinia` / `@pinia/nuxt` | `^3.0.4` / `^0.11.3` |
| `@nuxtjs/i18n` | `^10.2.3` (default: English) |
| TipTap | `3.29.2` (via `UEditor`; pin with `pnpm.overrides`) |
| Uppy | `^5.x` + `@uppy/vue` |
| Package manager | `pnpm@10.30.3` |

## Product references

- `prompt/specification/` — domain, APIs, permissions, flows
- Nested composables need **explicit imports** (e.g. `import { useConfirm } from '~/composables/common/useConfirm'`)
