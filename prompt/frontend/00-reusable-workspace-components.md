# Prompt 00A — Reusable Nuxt UI Workspace and Document Components

> **Status:** Implemented — architecture reference only (not a build ticket).
> Key code: `EntityWorkspaceView`, `EntityDocumentView`, `AppServerTable`, `AppKanban*`, `AppDocumentPage`, boards under `components/{meeting,record,portal}/`, card fields under `components/settings/`.
> Developer inventory: `frontend/docs/reusable-components-guide.md`.

## Reference (was copy/paste prompt)

Build the shared Docetra workspace and ERP-style document-page component system in the existing stack (Nuxt `^4.3.1`, Vue `^3.5.29`, TypeScript `^5.9.3`, Nuxt UI `^4.5.1`, Pinia `^3.0.4`, i18n `^10.2.3`, VueUse `^14.2.1`, TanStack Vue Table `^8.21.3` — see `prompt/frontend/README.md` Technology baseline). Inspect and reuse compatible components already present in `frontend/app/components`.

Use Nuxt UI primitives for the complete interface. Do not add another UI framework and do not copy ERPNext code or branding. Components must be typed, accessible, responsive, permission-aware, and API-agnostic.

Nuxt auto-imports by folder prefix (e.g. `components/common/AppLiveSearch.vue` → `CommonAppLiveSearch`). Prefer those prefixes in templates.

Assignment fields use `CommonAppMentionMultiInput`. Values are arrays and accept multiple people or organizations. Typing `@` or normal text searches the corresponding reference endpoint; Enter selects the highlighted result, duplicates are ignored, and selected values render as removable mention chips. Cards show officers in green, departments in blue, and partner companies in amber, with multiple names joined by commas.

The HTTP payload for every assignment is an array of `{ id, label, type }`, including a single selection. Option search is server-indexed, bounded, permission-filtered, and tenant-scoped; do not ship an unrestricted people directory to the browser.

## Page composition paths

```text
Generic CRUD list/detail
  → EntityWorkspaceView / EntityDocumentView
  → config in app/config/entities.ts

Special board UX (topics, stages, logs, upload)
  → App*Board in meeting|record|portal
  → domain composable (useMeetingTopicBoard, useRecordStageBoard, useRecordLogBoard, …)

Cross-entity archive
  → ArchiveWorkspaceView
  → useArchiveWorkspace + source entity adapters

Config admin (record types / attributes)
  → AppConfigEntityList + AppRecord*List / *Editor
  → useConfigListPage
```

## Workspace components

### `EntityWorkspaceView` / `EntityDocumentView`

Primary orchestrators for Organization, User Management, Meeting History, Portal Logs, System Logs, and Google Drive Sync (until dedicated UI lands). Thin pages pass `getEntityConfig('…')` only.

### `AppWorkspacePage`

Provide breadcrumb, localized title/description, result count, primary create action, overflow actions, sticky toolbar, and content slot. The create action navigates to the entity’s `/new` route.

The shared header reload icon calls the active page's own `refresh`/`load` function without changing routes. Workspace, board, configuration, dashboard, settings, and document pages publish their pending state through `AppHeaderPageActions`, show the icon as loading, and block duplicate refresh clicks until the current request finishes. A document refresh reloads the record and the related data handled by that page loader.

Do not expose Print actions in shared headers, document overflow menus, or role permission controls. Export opens one reusable dialog with optional start/end dates, scope (`all_matching`, `current_page`, or `selected`), and permission-safe field codes. The dialog emits a typed `ExportRequest`; the future export API must recheck record and field permissions before generating the file, while mock mode exercises the same request flow.

### `AppWorkspaceToolbar`

Provide debounced live search (`AppLiveSearch`), select/multiselect filters (`AppFilterSelect`), date range (`AppDateRangeFilter`), sort, and table/Kanban/hierarchy/timeline view toggle. Selected filters show an active grey border on the control (no filter chip row) via `utils/filter/select-ui.ts`. Synchronize supported state with URL query parameters via `useEntityWorkspace`.

Meeting History enables two modes over one list contract: the server-paginated table and `AppMeetingHistoryTimeline`. The timeline is vertical, orders cards from newest to oldest by `meetingDate`, and preserves search, filters, page size, page, loading, empty, error, retry, and document navigation. Its default request is `view=timeline&sort=-meetingDate`; HTTP APIs should accept the same query used by the mock adapter.

`AppDateRangeFilter` is the shared range control for toolbars, boards, exports, and archive filters. It delegates the calendar/time panel to `AppDatePickerPopover`, uses `utils/date-picker.ts` for canonical values, and adapts to constrained layouts: below 640 px or at `lg`/`xl` application font size, non-inline usage becomes an icon-triggered modal; `inline` usage remains a full-width input. Do not recreate paired date inputs in a page component.

### `ArchiveWorkspaceView`

The `/archive` workspace composes `AppWorkspacePage`, `AppServerTable`, `AppLiveSearch`, `AppSingleFilterSelect`, and `AppDateRangeFilter`. `useArchiveWorkspace` discovers only source entities the signed-in user may view, loads authorized archived and recoverably deleted rows, and exposes detail, `.restore`, confirmed administrator-only `.purge`, filtering, and paging actions. Owners may restore their own archived rows; only administrators may see or restore tombstones. Keep source-specific behavior behind the existing entity adapters. For production-scale archives, replace the bounded multi-source client aggregation with one authorized server-paginated archive query.

### `AppServerTable`

Generalize existing table primitives around TanStack Vue Table. Support server pagination, sorting, filtering, selection, sticky header, column visibility, **per-row action menus**, bulk actions, empty/error states, and responsive priority columns.

Props of note:

- `rowActions` — array of `RowActionItem`, or `false` to hide the menu. Default: Detail / Logs / Delete.
- `selectable` / `showMeta` — turn off for read-only audit lists.
- Dynamic cell render via `cell` on `TableColumnDef` (`text` | `badge` | `datetime` | `person`) with badge color logic for `action`, `severity`, `entityType`, `status`, `stage`.

Emit `rowAction` with `{ key, row }`. Row click still navigates to the document route; clicking `⋯` must not trigger row navigation.

### `AppRowActionsMenu`

Reusable `⋯` dropdown for any row/card:

```ts
interface RowActionItem {
  key: 'detail' | 'logs' | 'delete' | 'edit' | 'duplicate' | string
  labelKey?: string
  label?: string
  icon?: string
  color?: 'error' | 'primary' | 'neutral' | ...
  disabled?: boolean
  hidden?: (row: Record<string, unknown>) => boolean
}
```

Default actions (i18n under `docetra.rowActions.*`):

- **View detail** → open document / event
- **View logs** → `/records/record-logs` (optionally with search query)
- **Delete** → confirm then delete (omit when read-only)

Use on tables, cards, and boards. Prefer this over one-off dropdowns.

### Role permission matrix

`AppRolePermissionMatrix` is the only editor for structured role capabilities. It includes Dashboard and Archive alongside entity/configuration rows, normalizes API/mock rows through `utils/role/permissions.ts`, and supports per-action, per-row, Grant all, Clear all, creator-only scope, and access levels 0–9. Any non-view action implies View; clearing View clears the row. Configuration rows include Export because their list UI exposes export. On save, `useDocumentPage` sends normalized non-empty `permissionRows`, `permissionSchemaVersion: 1`, a namespaced flat `permissions` list, and `permissionCount`. Backend authorization remains authoritative and must recompute the expansion.

### `AppKanbanBoard` / `AppKanbanColumn` / `AppKanbanCard`

Reusable Jira / GitHub Projects–style board:

- Board area scrolls on **Y** when a column has many cards (toolbar stays fixed). Columns grow with cards; stages still scroll on **X**.
- Horizontal stage scrolling, drop-target highlight, drag-and-drop plus keyboard/menu “Move to stage”.
- Cards size to content (title, assignee, status/waiting, attachment/comment counts). Override via `#card` / `#column-header-actions` slots.
- Business-card status is exactly Active, Archived, or Deleted. Keep final workflow stages, account states, and job states in their own fields.
- Topic and meeting cards place permission-gated Delete in the `⋯` menu, use the shared confirmation dialog, and optimistically remove the card only after the adapter accepts the soft delete.
- Bounded per-column loading with “Load more”; optimistic move/rollback stays in the workspace composable.
- Card activation navigates to the canonical document route.

## Document-page components

### `AppDocumentPage`

Create the reusable full-page shell for new, detail, and edit routes. Compose it from Nuxt UI primitives such as `UPage`, `UPageHeader`, `UBreadcrumb`, `UTabs`, `UForm`, `UFormField`, `UButton`, `UBadge`, `UDropdownMenu`, `UCard`, `USeparator`, and responsive layout utilities available in the installed version. Document detail/create content is edge-to-edge (`p-0`); list workspaces keep `px-1.5 pt-1.5 pb-0`. For loading, use Nuxt UI defaults (`UTable` `:loading` or a light spinner)—do not build custom skeleton page components.

Provide:

- Sticky document header with breadcrumb, title, status, previous/next, overflow menu, and Save.
- Schema-driven tabs and sections.
- Main content column plus right metadata rail.
- Read, edit, loading, not-found, error, conflict, and permission-denied states.
- Unsaved-change protection for route navigation and browser close.
- Focus on the first invalid field after validation failure.
- Canonical navigation from `/new` to `/:id` after successful creation.

### `AppDocumentContentShell`

Readable max-width + gutters around form content (`wide` for dense forms).

### `AppDocumentForm`

Render schema-driven sections using responsive one- or two-column grids. Support section title, help text, visibility rules, read-only state, validation, dependent fields, and server validation error mapping. Avoid a single extremely long unstructured form.

### `AppDynamicFieldRenderer`

Render text, textarea, number, date, date-time, select, multi-select, boolean, organization, officer, record relation, file, URL, secret, connection-status, csv-list, builders, and **`card-fields-editor`** fields using Nuxt UI form controls / settings editors. Keep values typed and accessible.

### `AppDocumentMetaRail`

Provide reusable blocks for summary/avatar, assignment, attachments, tags, sharing, owner, created time, updated time, and permission-aware actions. Use a fixed desktop rail, a collapsible tablet region, and normal mobile flow. Lazy-load expensive blocks and keep every action backend-authorized.

### `AppCommentsActivity`

Render below the main document form:

- Comments heading.
- Current-user avatar and full-width comment composer.
- Explicit submit action with loading and validation.
- Activity heading with an optional right-side contextual action.
- Vertical chronological timeline with actor, action, target, and relative time.
- Expandable redacted metadata and safe links.
- Collapsible section and return-to-top control.

Use separate typed models:

```ts
interface EntityComment {
  id: string
  entityType: string
  entityId: string
  body: string
  author: PersonSummary
  createdAt: string
  editedAt?: string
}

interface ActivityEvent {
  id: string
  entityType: string
  entityId: string
  action: string
  actor?: PersonSummary
  summary: string
  occurredAt: string
  correlationId?: string
  metadata?: Record<string, unknown>
}
```

Activity is immutable. Escape untrusted content, redact sensitive metadata, cursor-paginate long timelines, and never expose backend-only audit payloads.

Shared table pagination includes a working rows-per-page selector for 10, 20, 50, 100, and All, resets to page 1 when the size changes, and shows the visible range (`X–Y of Z`) so small datasets do not make the selector appear broken.

Meeting and record board cards render configured metadata fields as compact, softly tinted highlight chips with an icon for every field. Keep semantic colors stable across cards: references/dates use info, people use success, organizations/duration warnings use warning, record type/mode use secondary, and long descriptive text uses neutral. Keep the title and status visually dominant, use stronger chips for body fields and smaller chips for footer facts, and preserve accessible contrast in light and dark themes so users can scan lists quickly.

### Attachments (document meta rail)

Attachments live on `AppDocumentMetaRail` (upload list + metadata), not a standalone panel. Pair with adapter `listAttachments` / `replaceAttachments`. Do not store binary content in Pinia.

### `AppRichTextNote`

Reusable TipTap editor via Nuxt UI `UEditor` + `UEditorToolbar` (HTML content). Client-only with loading fallback. Safe core extensions (align, color, highlight, resizable image); avoid duplicate Underline (StarterKit already includes it). Optional TableKit only when stable. Used for meeting notes and any future rich-text fields.

### `AppUppyUploader`

Reusable Uppy Dashboard for large uploads (XHR in API mode; local mock uploader when `useMockData`). Client-only mount (`AppUppyUploader.client.vue`). Emits `AttachmentMeta[]` on complete. Pair with adapter `listAttachments` / `replaceAttachments`. Include a fallback file picker if Dashboard fails to boot.

### `AppMeetingNotesDialog`

Fullscreen `UModal` for a meeting: TipTap notes (**3 cols**) + Uppy files (**1 col**). Header shows meeting title + date only. Save updates notes and attachments.

### `AppRecordLogBoard`

Record Logs index as a **1+3 split board** (not a plain workspace table):

- Left: vertical log-view tabs (All / Created / Updated / Stage / Shared / Incoming / Outgoing / Errors) with counts.
- Collapsible to icon-only rail (sidebar style) so the table gains width.
- Right: dynamic `AppServerTable` whose **columns + filters** change with the selected tab; `AppDateRangeFilter` + search in the toolbar; row action menu.
- Detail route: `/records/record-logs/:id`.

Composable: `useRecordLogBoard`.

### `AppFileUploadBoard`

Portal File Upload index as a **1+3 split board**:

- Left: Uppy upload folder (`AppUppyUploader` with `fill`); collapsible to icon-only rail like Logs.
- Right: uploaded-files `AppServerTable` with status filter + search; row actions Detail / Logs / Delete.
- Detail route: `/portal/file-upload/:id`.

### `AppRecordStageBoard`

Topic-style board for Incoming / Outgoing / Document / Master List Request:

- Left: workflow **Stages** rail (All + stage cards with counts); search stages; collapsible icon-only.
- Right: 3-column record **cards** with date range + search; drag onto a stage to move; `⋯` Detail / Logs / Move / Delete.
- Card scan fields driven by `useCardFields(entityKey)`.
- Stage rail driven by the selected Record Type's saved workflow stages and order; the static entity stage array is fallback-only.
- Dragging a card onto a configured stage and choosing **Move to stage** use the same transition action and refresh stage counts.
- Props: `dateField`, `subtitleField`, `stateKey`.

Composable: `useRecordStageBoard`.

### `AppMeetingTopicBoard`

Meeting Topic index as a **1+3 split board** (topics left, meetings right). Cards use `AppMeetingBoardCard` / `AppMeetingTopicSideCard` with config-driven slots. Notes via `AppMeetingNotesDialog`.

Composable: `useMeetingTopicBoard`.

### Card fields (settings → boards)

| Piece | Role |
| --- | --- |
| `AppCardFieldsEditor` / `AppCardFieldPreview` | App Config Display tab UI |
| `useCardFields` | Resolve visible slots + footer align per entity |
| `utils/card-fields.ts` | Slot catalogs + defaults for meeting/record entities |

### `useEntityWorkspace`

Coordinate workspace URL state, table/board mode, search, filters, sorting, pagination/cursors, refresh, request cancellation, optimistic board transitions, and **row action handlers** (detail / logs / delete). Accept typed adapters instead of hardcoded endpoints.

### `useDocumentPage`

Coordinate route identity, create/read/edit state, schema, initial values, dirty tracking, validation, save, conflict handling, lazy tab data, comments, activity, permissions, and previous/next navigation. Accept entity adapters and do not invent endpoints inside UI components.

### `useRecordTypeDrivenTabs`

This composable is the current form-schema resolver for every entity marked `recordBacked: true`, including meetings, meeting topics, incoming/outgoing documents, documents, and master-list requests. It resolves the published schema by `recordTypeId` or configured stable code, caches it briefly, injects assigned sections into the shared Details tab, resolves workflow-stage options, and prunes values only when the user intentionally changes record type. Extend the same resolved-schema result to list/filter/search/card/export eligibility without reintroducing an entity-key allowlist or pruning inaccessible/temporarily hidden values.

### `useMenu` / `useUserMenu`

- `useMenu` — sidebar links only (no System Monitor group). Order: Dashboard → Meeting → Record → Organization → Portal → User Management → Configuration → Settings. Filter links with the same namespaced `.view` capabilities used by route metadata and remove empty groups.
- `useUserMenu` — user profile, Archive, System Log, Language, Font size, About, Appearance, and Logout. The identity item opens `AppUserProfileDialog`; avatar mutations use the auth adapter and update the auth store immediately.

### `useGlobalSearch`

Cmd+K keyword / semantic search over the local index; permission-filtered groups; Ask AI on demand.

## Shared interaction contract

- Add navigates to `/module/entity/new`.
- A table row or Kanban card navigates to `/module/entity/:id`.
- Row `⋯` → Detail / Logs / Delete (or page-specific actions) via `AppRowActionsMenu`.
- Save stays on the document page and refreshes only affected data.
- Successful creation replaces `/new` with the canonical ID route.
- Cancel or Back returns to the preserved workspace URL when safe.
- Unsaved changes require confirmation (`useConfirm`).
- Previous/next respects the source workspace ordering where available.
- Backend authorization is authoritative; frontend permission checks control visibility only.
- Shared permission derivation uses `utils/role/access.ts`: `.view` is the namespace root for `.create`, `.edit`, `.archive`, `.restore`, `.delete`, `.purge`, `.comment`, `.export`, and other supported actions. `.purge` is never creator-scoped.
- `AppDocumentPage` accepts `readOnly`, `canSave`, `canComment`, and `canExport`; `EntityWorkspaceView` derives create/delete/export visibility from the entity permission namespace.
- `AppServerTable.canSelectRow` supports mixed-permission tables such as Archive; hidden row actions and disabled selection must agree.
- Specialized boards must hide and disable the interaction itself: no draggable record without `.transition`, no meeting assignment/reorder without `.assign`, and no meeting notes editor without `.edit`.
- Denied routes and API `403` responses open the localized global access dialog over the current or first authorized page. Expired API sessions (`401`) clear authentication and show the session-expired dialog on sign-in; do not create a dedicated forbidden page.
- Use `usePathModel` for schema field access and `useAppPageTitle` for the repeated Settings title/SEO lifecycle.

## Reusable security components

- `utils/security/url.ts` is the shared URL boundary. It rejects executable schemes, protocol-relative internal links, and authenticated cross-origin API/upload endpoints.
- `utils/security/files.ts` centralizes safe raster types and default document-upload rules.
- `AppUppyUploader` exposes `maxFileSizeMb`, `maxNumberOfFiles`, and `allowedFileTypes`, applies them to both Uppy and fallback picker flows, and never sends Authorization outside the API origin.
- `AppImageUploadField`, `AppRichTextNote`, and `ResizableImageView` use the shared raster/source checks. Backend MIME sniffing, malware scanning, storage isolation, and authorization are still mandatory.

## Acceptance

Add focused tests for URL state, pagination, stage rollback, document routing, unsaved changes, validation focus, create-to-detail navigation, comment submission, activity rendering, and row action menus. Run typecheck and production build. The shared system is already used across Meeting, Record, Organization, Portal, and User Management pages.
