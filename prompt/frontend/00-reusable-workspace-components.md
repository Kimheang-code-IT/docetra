# Prompt 00A — Reusable Nuxt UI Workspace and Document Components

> **Status:** Implemented — architecture reference only (not a build ticket).
> Key code: `EntityWorkspaceView`, `EntityDocumentView`, `AppServerTable`, `AppKanban*`, `AppDocumentPage`, boards under `components/{meeting,record,portal}/`, card fields under `components/settings/`.
> Developer inventory: `frontend/docs/reusable-components-guide.md`.

## Reference (was copy/paste prompt)

Build the shared Docetra workspace and ERP-style document-page component system in the existing stack (Nuxt `^4.3.1`, Vue `^3.5.29`, TypeScript `^5.9.3`, Nuxt UI `^4.5.1`, Pinia `^3.0.4`, i18n `^10.2.3`, VueUse `^14.2.1`, TanStack Vue Table `^8.21.3` — see `prompt/frontend/README.md` Technology baseline). Inspect and reuse compatible components already present in `frontend/app/components`.

Use Nuxt UI primitives for the complete interface. Do not add another UI framework and do not copy ERPNext code or branding. Components must be typed, accessible, responsive, permission-aware, and API-agnostic.

Nuxt auto-imports by folder prefix (e.g. `components/common/AppLiveSearch.vue` → `CommonAppLiveSearch`). Prefer those prefixes in templates.

## Page composition paths

```text
Generic CRUD list/detail
  → EntityWorkspaceView / EntityDocumentView
  → config in app/config/entities.ts

Special board UX (topics, stages, logs, upload)
  → App*Board in meeting|record|portal
  → domain composable (useMeetingTopicBoard, useRecordStageBoard, useRecordLogBoard, …)

Config admin (record types / attributes)
  → AppConfigEntityList + AppRecord*List / *Editor
  → useConfigListPage
```

## Workspace components

### `EntityWorkspaceView` / `EntityDocumentView`

Primary orchestrators for Organization, User Management, Meeting History, Portal Logs, System Logs, and Google Drive Sync (until dedicated UI lands). Thin pages pass `getEntityConfig('…')` only.

### `AppWorkspacePage`

Provide breadcrumb, localized title/description, result count, primary create action, overflow actions, sticky toolbar, and content slot. The create action navigates to the entity’s `/new` route.

### `AppWorkspaceToolbar`

Provide debounced live search (`AppLiveSearch`), select/multiselect filters (`AppFilterSelect`), date range (`AppDateRangeFilter`), sort, and table/Kanban/hierarchy view toggle. Selected filters show an active grey border on the control (no filter chip row) via `utils/filter/select-ui.ts`. Synchronize supported state with URL query parameters via `useEntityWorkspace`.

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

### `AppKanbanBoard` / `AppKanbanColumn` / `AppKanbanCard`

Reusable Jira / GitHub Projects–style board:

- Board area scrolls on **Y** when a column has many cards (toolbar stays fixed). Columns grow with cards; stages still scroll on **X**.
- Horizontal stage scrolling, drop-target highlight, drag-and-drop plus keyboard/menu “Move to stage”.
- Cards size to content (title, assignee, status/waiting, attachment/comment counts). Override via `#card` / `#column-header-actions` slots.
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

For record entities (`incomingDocuments`, `outgoingDocuments`, `documents`, `masterListRequests`), merge static document tabs with attributes from the selected record type (catalog via configuration repositories).

### `useMenu` / `useUserMenu`

- `useMenu` — sidebar links only (no System Monitor group). Order: Dashboard → Meeting → Record → Organization → Portal → User Management → Configuration → Settings.
- `useUserMenu` — System Log, Language, Font size, About, Appearance, Logout.

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

## Acceptance

Add focused tests for URL state, pagination, stage rollback, document routing, unsaved changes, validation focus, create-to-detail navigation, comment submission, activity rendering, and row action menus. Run typecheck and production build. The shared system is already used across Meeting, Record, Organization, Portal, and User Management pages.
