# Docetra Product UI Design Map

> **Status:** Implemented — architecture reference only (not a build ticket).
> Reflects current `frontend/` code (Nuxt 4 + Nuxt UI 4 shell).

## What the product data means for the UI

Docetra is a record-centered operational system. **Product source of truth:** `prompt/idea/` (business intent + draft DB) and `prompt/specification/` (engineering contracts). This UI map only covers presentation.

Business pages reuse four concepts:

1. **Entity workspace** — searchable, filterable, server-paginated table data (`EntityWorkspaceView` + `entities.ts`).
2. **Workflow board** — the same records grouped by stage with controlled movement (`AppRecordStageBoard`, meeting topic board).
3. **Document page** — a dedicated route for create, detail, and edit (`EntityDocumentView` / `AppDocumentPage`).
4. **Conversation and history** — comments, emails, activity, changes, and audit evidence.

Use only Nuxt UI components and existing project dependencies. Do not introduce another UI kit or copy ERPNext source code. Recreate the useful information architecture with Docetra styling and reusable Vue components.

## View-selection rules

| Page type | Primary views | Create/detail/edit | Comments/activity |
|---|---|---|---|
| Workflow records | **Topic-style 1+3 stage board** (Incoming / Outgoing / Document / Master List Request) | Full document page; fields resolve from the published **record type** | Comments + activity |
| Meeting topics | Topic/meeting split board (1+3); notes fullscreen dialog (TipTap 3.29 notes **3 cols** + Uppy 5 files **1 col**) | Full document page using the same record-type field resolver | Comments + activity |
| Meeting history | Switchable server-backed **table** and **vertical timeline cards** (newest meeting first, top to bottom) | Full meeting document page | Comments + activity |
| Organization master data | Table; hierarchy/card view where useful | Full document page | Activity; comments where collaboration helps |
| Users and roles | Table | Full document page or permission editor page using the same wide content shell as Settings for add/detail/edit | Security activity; no casual comments |
| Archive | Cross-entity table with search, type/date filters, restore, detail, and confirmed permanent deletion | Opens the original entity detail route | Source entity activity |
| Configuration reference data | Table | Full document page | Comments + immutable configuration activity |
| Upload and sync operations | File Upload: **1+3 split** (Uppy left + table right); Drive Sync: status + table (dedicated UI still open) | Full detail/configuration page | Job/file activity |
| Logs and history | Read-only **1+3 split board** (`/records/record-logs`) or table; System Log via user menu | Read-only event page | Activity itself; no comment composer |
| Dashboard | KPI and aggregate widgets | No create page | Recent activity feed |
| Authentication | Focused form | Dedicated auth page under `/auth/*` | None |

Department Ancestor is a self-join selector. Options are tree ordered and prefixed with one spaced `-` per user-created depth (`- Child`, `- - Sub-child`, `- - - Third level`, continuing without a fixed depth limit). Edit mode excludes the current department and its complete descendant subtree, and both frontend and API validation reject cycles.

Kanban is used only when an entity has meaningful workflow stages.

## ERP-style document page

Add, row click, and Kanban card click navigate to dedicated routes:

- Create: `/module/entity/new`
- Detail: `/module/entity/:id`
- Edit uses the same `:id` document page with editable fields when permitted.

The desktop layout contains:

- Sticky top header with breadcrumb, document title, status badge, previous/next navigation, overflow actions, and primary Save action (`useAppHeader` + `AppHeaderPageActions`).
- Horizontal section tabs generated from the document schema (record types inject extra sections via `useRecordTypeDrivenTabs`).
- Main content area with readable maximum width (`AppDocumentContentShell`) and two-column field grids.
- Section cards or bordered sections with headings, descriptions, fields, child tables, and relationship lists.
- Persistent right metadata rail for summary/avatar, assignment, attachments, tags, sharing, ownership, created/updated metadata, and permission-aware quick actions.
- Comments composer and chronological Activity timeline below the main form.

On tablet, the metadata rail becomes a collapsible section below the header. On mobile, tabs become a select or horizontally scrollable tabs, field grids become one column, and sticky actions remain reachable.

Create mode may hide history-only sections until the first successful save. After creation, navigate to the canonical `:id` route. Detail and edit use the same schema so fields are not duplicated across separate implementations.

All unified-record pages use the Attribute Catalog and resolved-schema contract in `00C-dynamic-record-fields.md`. Add, detail, and edit are different modes of one versioned schema. Meeting fields are not a separate hardcoded system. Dynamic fields that opt into list, filter, search, card, or export use are exposed through the same permission-filtered schema.

## Comments and activity reference

Match the supplied reference pattern inside the document page:

- “Comments” heading.
- Current-user avatar followed by a wide reply/comment input.
- “Activity” heading with an optional contextual action such as “New Email”.
- A vertical chronological timeline showing actor, action, target, and relative time.
- Expandable event metadata.
- A bottom-right collapse/scroll-to-top control.

Comments and system activity are separate datasets. Comments can be created; activity is immutable and generated by the backend.

## Board cards (config-driven scan fields)

Meeting and record board cards show **summary + important scan fields** from App Config → Display → card fields (`AppCardFieldsEditor`, `useCardFields`, `utils/card-fields.ts`):

- Prefer core identity fields when configuring: `title`, `status`, stage, tags, time, content/summary.
- Title is always shown; other slots are selectable per entity (meeting topics/history, incoming/outgoing/documents/master list).
- Footer slot alignment is configurable per entity.
- Saving App Config invalidates the card-fields cache so boards refresh without a full reload.

## Large-data rules

- Never download an entire enterprise dataset for client filtering.
- Persist filters, sort, page/cursor, and view mode in the workspace URL.
- Meeting History supports `view=table|timeline`; both modes use the same filters and pagination, and request `sort=-meetingDate` by default so a future API preserves the top-to-bottom chronology across pages.
- Use server pagination for tables and incremental loading for Kanban columns.
- Lazy-load document tabs, relationship tables, comments, and activity.
- Cancel stale requests and protect against out-of-order responses.
- Use stable IDs and optimistic updates only with rollback.
- Keep board columns bounded and provide “Load more”.
- Make exports asynchronous when the result is large.
- Every workspace and document page needs loading, empty, error, retry, permission-denied, and partial-data states.
- Prefer Nuxt UI default loading (`UTable` `:loading`, light spinner). Do not invent custom full-page skeleton kits.
- App version comes only from `NUXT_PUBLIC_APP_VERSION` / `runtimeConfig.public.appVersion` and is shown in About.
- List pages use `px-1.5 pt-1.5 pb-0`; document detail/create pages use `p-0`.
- Record / Portal page titles are plural **Logs** (`/records/record-logs`, `/portal/portal-logs`).
- System Log is opened from the user menu, not the sidebar.
- Archive is opened from the user menu and aggregates only source entities the user may view.
- The user identity opens the shared profile dialog for avatar, password, and effective-permission views; it is not a separate settings page.
- Date/date-time inputs and ranges use the shared picker utilities. Toolbar ranges collapse to an icon/modal on small screens or at large application font sizes.
- English uses Inter first; Khmer uses Noto Sans Khmer first. All layouts must remain usable at the persisted 14, 16, 18, and 20 px root font sizes.
- Table rows expose a reusable `⋯` menu (`AppRowActionsMenu`) for Detail, Logs, and Delete when permitted.
- **Cmd+K** opens app-wide search (`useGlobalSearch`); it does not replace per-page `AppLiveSearch` toolbars.
- Sidebar links and document/list actions are capability-filtered, but backend authorization remains authoritative.
- Authenticated API/upload traffic stays on the configured API origin; external meeting links allow HTTP(S) only and inline image previews allow safe raster formats only.

## Split boards (1+3)

Used by Meeting Topics, Record Logs, File Upload, and Record stage boards (Incoming / Outgoing / Document / Master List Request):

- Always side-by-side: left rail + right main pane (never stack the left rail above the content on desktop).
- Left can collapse to an **icon-only** rail so the main pane gains width.
- Right header: collapse toggle + title on the left; date range / search (or status + search) on the right (no subtitle under the title). Use `AppDateRangeFilter` for date ranges.
- Comfortable header padding (`px-4 py-3.5`).
- File Upload left rail hosts Uppy; Logs left rail hosts view tabs; Record boards host workflow stages; Topics host topic cards.
