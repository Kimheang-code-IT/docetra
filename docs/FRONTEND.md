# Docetra — Frontend

Nuxt 3 (Vue 3 + TypeScript + Pinia) in `frontend/`. English + Khmer i18n (`i18n/`). Tests: Vitest (9 files, 79 tests), Playwright configured.

## Architecture

```
Page / Component
      ↓
Composable / Store        (useEntityApis, useMeetingTopicBoard, useDocumentPage, …)
      ↓
Repository / API Adapter  (config/entities.ts, composables/api/*, repositories/http/*)
      ↓
useApi()                  (single HTTP client: cookies, CSRF, error policy, concurrency)
      ↓
/api/v2
```

Rules enforced in code:
- **All** HTTP through `useApi()` / entity adapters — no component-level `$fetch`/axios.
- Endpoint constants centralized in `app/utils/constants/api-endpoints.ts`.
- Optimistic concurrency: `withConcurrencyToken(payload, version)` sends `If-Match`.
- Menus/routes derive from `GET /records/_meta/surfaces` (active record types + `uiSurface`), cached per-identity in `localStorage` with background revalidation.
- New user-facing text requires `en` + `km` keys.
- `AuthUser.permissions` gates presentation only.

## Central entity config (`app/config/entities.ts`, 1119 lines)

Single source defining every workspace page: `routeBase`, `titleKey`, `permission`, `views` (table/kanban), `recordTypeCode`, `stages`, `columns`, `filters`, `tabs`, `formFields` (type/required/colSpan/selects with optionsEndpoint), `rowActions`, `detail` fields.

Entity keys → adapters (`composables/api/useEntityApis.ts`):

| Key | API | Page |
|---|---|---|
| meetingTopics | records/meeting_topic | /meetings/topics |
| meetingHistory | records/meeting_history | /meetings/history |
| incomingDocuments | records/incoming_document | /records/incoming-documents |
| outgoingDocuments | records/outgoing_document | /records/outgoing-documents |
| documents | records/document | /records/documents |
| masterListRequests | records/master_list_request | /records/master-list-requests |
| recordLogs | records/logs | /records/logs |
| departments / companies | organizations/department·company | /organizations/… |
| purposes / sectors | /purpose, /sector | /purpose, /sector |
| officers | /officers | /officers |
| roles / users | /users/roles, /users | /user-management/… |
| recordTypes / recordAttributes | /configuration/… | /configuration/… |
| fileUploads | /portal/file-uploads | /portal/file-upload |
| googleDriveSync | /portal/google-drive-sync | /portal/google-drive-sync |
| portalLogs / systemLogs | /portal/logs, /system/logs | /portal/portal-logs, /system-monitor/… |

Log adapters wrap the audit DTO mapper (`utils/audit/audit-dto.ts`) — one canonical backend audit contract mapped to portal/system views centrally.

## Auth/session (`stores/auth.ts`, `utils/auth/*`, `utils/api/error-policy.ts`)

- Cookie session mode (default): JWTs in HttpOnly cookies; bearer mode opt-in (`authMode==='bearer'`, small token cookie only — profile never in a cookie).
- Stored user paints the shell immediately; `/auth/me` validates in background; refresh on 401; timeout/5xx does not destroy a valid local session; 403 never logs out.
- Session events broadcast across tabs (`utils/auth/session-sync.ts`).
- Login error mapping (`login-errors.ts`), password reset flow pages (`auth/forget-password|reset-password|verify-code`).

## Page inventory

| Page(s) | Purpose | Composables / components |
|---|---|---|
| `/` | Dashboard KPIs, stage charts, recent events | reporting composables |
| `/meetings/topics` | Topic rail + meeting cards, assign/unassign, reorder, complete | `useMeetingTopicBoard`, `AppMeetingTopicBoard`, `AppMeetingTopicNameDialog`, `AppMeetingHistoryTimeline`, `AppMeetingNotesDialog`, `AppMeetingDriveFilePicker` |
| `/meetings/history` (+new/[id]) | Meeting records list/board/detail | `EntityWorkspaceView`, `EntityDocumentView` |
| `/records/{incoming-documents,outgoing-documents,documents,master-list-requests}` (+new/[id]) | Document workspaces | `EntityWorkspaceView`, `EntityDocumentView`, `useDocumentPage`, `AppDynamicFieldRenderer` |
| `/records/logs` | Cross-type record audit | `useRecordLogBoard`, `AppRecordLogBoard` |
| `/organizations/{department,company}` (+new/[id]) | Org management | `useEntityWorkspace` |
| `/purpose`, `/sector` (+new/[id]) | Classification catalogs | `useEntityWorkspace` |
| `/officers` (+new/[id]) | Officer management | `useEntityWorkspace` |
| `/portal/file-upload` (+[id]) | File management | `AppFileUploadBoard` |
| `/portal/google-drive-sync` (+new/[id]) | Drive sources/sync/jobs | `AppGoogleDriveSync` |
| `/portal/portal-logs` (+[id]) | Portal audit | audit DTO mapper |
| `/user-management/roles` (+new/[id]) | Role + permission matrix | permission-catalog contract |
| `/user-management/users` (+new/[id]) | Users ↔ officers | `useEntityWorkspace` |
| `/configuration/record-types` (+new/[id]) | Type + stages + permissions editor | `AppRecordTypeEditor/List`, `AppWorkflowStageBuilder`, `AppValidationRuleBuilder`, `AppVisibilityRuleBuilder`, `AppNumberingPreview` |
| `/configuration/record-attributes` (+new/[id]) | Attribute catalog | `AppRecordAttributeEditor/List`, `AppAttributeOptionsBuilder` |
| `/settings/app-info|app-config|storage` | System settings | `useAppBranding`, `useAppLocalization`, `useAppRuntimeConfig`, settings-storage repo |
| `/archive` | Cross-source archive/restore | `ArchiveWorkspaceView`, `useArchiveWorkspace` |
| `/system-monitor/system-logs` (+[id]) | System audit | audit DTO mapper |
| `/auth/*` | Login, forgot/verify/reset password | `useAuthApi` |

## Workspace patterns

- **List/table + kanban**: `AppWorkspaceBoardPage`, `AppServerTable`, `AppKanbanBoard` (server-side pagination/filter/sort; page sizes from `TABLE_PAGE_SIZES`).
- **Detail**: `EntityDocumentView` + `useDocumentPage` — tabs (details, related, files, activity/history, permissions), meta rail, optimistic updates, neighbors paging.
- **Stage board**: `AppRecordStageBoard` / `useRecordStageBoard` — one request per board dataset, drag → `PATCH .../stage`.
- **Record surfaces**: `useRecordSurfaces` boot catalog → menus + dynamic routes `/records/{typeCode}`, `/meetings/{typeCode}`; resolve by code/slug/routeBase suffix.
- **Archive**: sources = meetingTopics, meetingHistory, incoming/outgoingDocuments, documents, masterListRequests; permission-filtered; restore with concurrency token.

## i18n

All labels via `labelKey` → `docetra.*` keys; `en.json` + `km.json`. Date/number formatting via `useAppLocalization`.
