# Docetra Frontend Prompts

Architecture references for the Docetra v2 UI in `frontend/`. Align product presentation with `prompt/idea/` and `prompt/specification/`; this folder only describes how the current Nuxt app is built.

## Status

Most page prompts are **removed** — those routes already have working UI and logic (mock adapters / repositories).

| Area | Status |
| --- | --- |
| Shared shell, workspace kit, config/settings kit | Done — see `00-*.md` as architecture reference |
| Dynamic Attribute Catalog + record schemas | Frontend/mock flow implemented; HTTP backend remains — see `00C-dynamic-record-fields.md` |
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
| [`00C-dynamic-record-fields.md`](./00C-dynamic-record-fields.md) | Attribute Catalog, record-type field composition, runtime schemas, and API-ready dynamic values |

Developer inventory (code-side): `frontend/docs/reusable-components-guide.md`.

Backend handoff documents: [`../backend/00-integration-contract.md`](../backend/00-integration-contract.md), `frontend/docs/api-integration-guide.md`, and `frontend/docs/local-frontend-docker-backend.md`.

## Implemented route inventory

| Nav | Page | Route | Main implementation |
| --- | --- | --- | --- |
| — | Dashboard | `/` | `pages/index.vue` |
| User menu | Archive | `/archive` | `ArchiveWorkspaceView` + `useArchiveWorkspace` |
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
- **All record-backed forms:** use the system-wide contract in `00C-dynamic-record-fields.md`. `useRecordTypeDrivenTabs` activates from `recordBacked` entity metadata, resolves by record-type ID or stable code, and injects published fields for Meetings, Meeting Topics, and Record entities. Schema-driven list/filter/search/card/export eligibility remains the next extension.
- **Board cards** (meeting + record): visible slots / footer align come from App Config display → `useCardFields` + `AppCardFieldsEditor`.
- **Lifecycle status:** business cards/forms expose only Active, Archived, and Deleted. Workflow stage, user-account state, publication state, and job state are separate typed fields; no page adds Completed to the business Status select.
- **Multi-assignment:** assignment fields always hold arrays and use `CommonAppMentionMultiInput`. Typing `@` or normal text searches permission-filtered officers, departments, and companies; cards render one or many names and removable typed tags.
- **Meeting/topic deletion:** each card's `⋯` menu exposes Delete only with its `.delete` capability, confirms through `useConfirm`, and uses soft delete in API mode.
- **Meeting creation:** Meeting History is browse-only for creation; **New Meeting** starts from the Meeting Topic board so the topic context is preserved.
- **Cmd+K global search:** `layouts/default.vue` + `useGlobalSearch` (keyword / semantic; Ask AI on demand). Page toolbars keep local `AppLiveSearch`.
- **Archive workspace:** `/archive` requires `archive.view` and aggregates only authorized archived or recoverably deleted source rows. Owners may restore their own archived rows with `.restore`; normal `.delete` creates an administrator-recoverable tombstone; irreversible row/bulk purge requires administrator `.purge` plus retention/dependency confirmation.
- **Responsive date controls:** `AppInputDate`, `AppDateRangeFilter`, and `AppDatePickerPopover` share parsing/serialization through `utils/date-picker.ts`. Compact toolbars use an icon-triggered modal on small screens or with large font preferences; inline form/dialog usage remains full width.
- **User profile:** selecting the user identity opens `AppUserProfileDialog` for profile, password, and effective-permission views. Avatar upload/remove uses `adapters/auth.ts`, accepts safe raster images up to 2 MB, and updates `stores/auth.ts` immediately.
- **User preferences:** locale + font size (`stores/preferences.ts`); appearance via color mode; Archive / System Log / About / Logout from `useUserMenu`. English uses Inter first; Khmer uses Noto Sans Khmer first.
- **Data mode:** this release uses mock repositories by default in every environment. `runtimeConfig.public.useMockData` remains the API-ready switch; set `NUXT_PUBLIC_USE_MOCK_DATA=false` later when the HTTP backend is available.
- **Backend handoff:** follow `frontend/docs/api-integration-guide.md` and `prompt/backend/00-integration-contract.md`; pages remain unaware of mock/HTTP mode, endpoint strings stay in `ApiEndpoints`, and `$fetch` stays inside `useApi`.

## Current security and API-ready contract

- `AuthUser.permissions` is the authoritative flat capability list when present; legacy `pageAccess` remains a compatibility fallback, and `pageAccess: ['ALL_PAGES']` keeps administrator sessions unrestricted. Dashboard and Archive are explicit role-matrix rows (`dashboard.view`, `archive.view`).
- `middleware/auth.global.ts` enforces route `definePageMeta.permission`; `useMenu`, `useUserMenu`, search, and shared actions use the same keys. Denied routes and API `403` responses open the global access dialog, while API `401` responses clear the expired session and show the session-expired dialog on sign-in. No dedicated forbidden page is used.
- `/new` routes require the corresponding `.create` capability. Shared list/document components independently gate `.edit`, `.archive`, `.restore`, `.delete`, `.purge`, `.comment`, `.export`, and `.configure` actions. Role and user detail surfaces also expose activity and permission-gated comments; deleting your own account disables it and revokes sessions instead of physically removing identity history.
- Specialized UIs apply equivalent gates: File Upload (`create`/`delete`), record boards (`transition`/`delete`), meeting assignment/reorder (`assign`), meeting notes (`edit`), configuration lists (`create`/`delete`/`export`/`configure`), Archive source actions, comment management, and Logs links.
- Permission checks in the browser improve UX only. Every HTTP endpoint must authenticate and authorize the requested record, action, field, and tenant scope again.
- `useApi` permits authenticated requests only to the configured API origin. It uses credentialed cookies and CSRF protection in production mode; `AppUppyUploader` enforces the same boundary.
- External meeting links allow only HTTP(S); application navigation accepts only root-relative paths.
- Inline images allow raster PNG/JPEG/WebP/GIF only. SVG and executable URL schemes are rejected. Upload restrictions are reusable and must also be enforced by the API.
- Production mode expects an `HttpOnly`, `Secure` backend session cookie and a readable double-submit CSRF cookie. JavaScript bearer tokens are limited to mock/explicit legacy mode; `/auth/me` refreshes the frontend's sanitized session snapshot.
- Production responses set `nosniff`, strict referrer policy, frame denial, and a restrictive permissions policy. DevTools are development-only.
- Shared schema forms use `usePathModel`; Settings page title/SEO lifecycle uses `useAppPageTitle`. Do not recreate these patterns in route components.

## Technology baseline

Align with `frontend/package.json` (do not invent newer majors):

| Package | Version |
| --- | --- |
| `nuxt` | `^4.3.1` |
| `vue` | `^3.5.29` |
| `@nuxt/ui` | `^4.5.1` |
| `tailwindcss` | `^4.2.1` |
| `@nuxt/image` | `^2.0.0` |
| `@nuxt/fonts` | `^0.14.0` |
| `pinia` / `@pinia/nuxt` | `^3.0.4` / `^0.11.3` |
| `@nuxtjs/i18n` | `^10.2.3` (default: English) |
| `@internationalized/date` | `^3.12.0` |
| `@vueuse/core` / `@vueuse/nuxt` | `^14.2.1` |
| TipTap | `3.29.2` (via `UEditor`; pin with `pnpm.overrides`) |
| Uppy | `^5.x` + `@uppy/vue` |
| ECharts / `vue-echarts` | `^6.0.0` / `^8.0.1` |
| Zod | `^4.3.6` |
| Package manager | `pnpm@10.30.3` |

## Product references

- `prompt/specification/` — domain, APIs, permissions, flows
- Nested composables need **explicit imports** (e.g. `import { useConfirm } from '~/composables/common/useConfirm'`)
