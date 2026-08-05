# Docetra Frontend — Reusable Components Guide

> Inventory of what to reuse, what to keep feature-local, and how to write high-performance Vue/Nuxt code in this repo.
>
> Code roots: `frontend/app/components`, `frontend/app/composables`, `frontend/app/utils`.
> Related architecture: `prompt/frontend/00-reusable-workspace-components.md`.

---

## 1. Quick rules


| Do                                                                                                      | Don’t                                                                              |
| ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Prefer existing `common/*`, `workspace/*`, `document/*` shells before inventing new UI                  | Copy-paste toolbar/search/filter into a new page                                   |
| Drive lists/docs with `EntityConfig` + `EntityWorkspaceView` / `EntityDocumentView` when the UX matches | Force every feature into Entity* if the UX is a board/rail (use a dedicated board) |
| Put shared styles for filters in `utils/filter/select-ui.ts`                                            | Hard-code ring/border classes in each page                                         |
| Keep domain cards in `meeting/` / `record/` / `configuration/`                                          | Move meeting-only cards into `common/` “just in case”                              |
| Use `useConfirm`, `useAppHeader`, composables for state                                                 | Duplicate confirm dialogs or header action wiring                                  |


**Reuse test:** If two features need the same control and the props stay generic (no entity-specific fields), it belongs in `common/` or `workspace/`. If the card knows about topics, stages, or record types, keep it feature-specific.

---



## 2. How pages are built (choose the right path)

```text
Generic CRUD list/detail
  → EntityWorkspaceView / EntityDocumentView
  → config in app/config/entities.ts

Special board UX (topics, stages, logs, upload)
  → App*Board in meeting|record|portal
  → domain composable (useMeetingTopicBoard, useRecordStageBoard, …)

Config admin (record types / attributes)
  → AppConfigEntityList + AppRecord*List / *Editor
  → useConfigListPage
```

Nuxt auto-imports components by folder:


| Folder                  | Template prefix                      |
| ----------------------- | ------------------------------------ |
| `components/common/`    | `CommonApp…`                         |
| `components/workspace/` | `WorkspaceApp…` / `WorkspaceEntity…` |
| `components/document/`  | `DocumentApp…` / `DocumentEntity…`   |
| `components/meeting/`   | `MeetingApp…`                        |
| `components/record/`    | `RecordApp…`                         |
| `components/layout/`    | `LayoutApp…`                         |


---



## 3. Reusable components (prefer these)



### 3.1 Filters & toolbar


| Component               | When to use                               | How                                                                              |
| ----------------------- | ----------------------------------------- | -------------------------------------------------------------------------------- |
| `AppLiveSearch`         | Any live search box                       | `v-model` + `placeholder` + optional `size`. Active grey border via `select-ui`. |
| `AppFilterSelect`       | Entity `FilterDef` (select / multiselect) | Pass `filter` + `v-model`. Wraps single/multi internals.                         |
| `AppSingleFilterSelect` | One value (status, sort)                  | `items: { label, value }[]` + `v-model`.                                         |
| `AppMultiSelect`        | Multi value filter                        | Same items shape; optional `showNoneOption`.                                     |
| `AppInputDate`          | Date or date-time field/filter            | `v-model`, `granularity: 'day' | 'minute'`, …                                    |
| `AppInputDateRange`     | Start–end filter pair                     | `v-model:start` / `v-model:end`.                                                 |
| `AppWorkspaceToolbar`   | Standard list toolbar                     | search, filters, sort, view tabs; emit `setFilter` / `update:*`.                 |


**Shared styling:** `utils/filter/select-ui.ts`

- `getFilterSelectUi(active)`, `getFilterSearchUi(active)`, `getFilterDateUi(active)`
- `isFilterValueActive(value)`
- Active border = default grey (`ring-default`), not primary/black

```vue
<CommonAppLiveSearch v-model="search" :placeholder="t('common.search')" />
<CommonAppFilterSelect
  :filter="statusFilter"
  :model-value="statusValue"
  @update:model-value="onStatus"
/>
```



### 3.2 Workspace list / board primitives


| Component                            | When to use                                         |
| ------------------------------------ | --------------------------------------------------- |
| `AppWorkspacePage`                   | Page chrome: title, create/refresh, content slot    |
| `AppServerTable`                     | Server-paginated table (TanStack)                   |
| `AppRowActionsMenu`                  | `⋯` Detail / Logs / Delete (or custom `rowActions`) |
| `AppKanbanBoard` / `Column` / `Card` | Stage kanban inside Entity workspace                |
| `AppTableRowMeta`                    | Owner / updated / comment counts in table rows      |


```vue
<WorkspaceEntityWorkspaceView :config="entityConfigs.departments" />
```

For a custom table without EntityWorkspace:

```vue
<WorkspaceAppServerTable
  :columns="columns"
  :rows="rows"
  :total="total"
  :page="page"
  :limit="limit"
  :pending="pending"
  :error="error"
  @update:page="page = $event"
  @row-click="openRow"
  @row-action="onRowAction"
/>
```



### 3.3 Document page stack


| Component                 | When to use                                                             |
| ------------------------- | ----------------------------------------------------------------------- |
| `EntityDocumentView`      | Standard entity create/edit/detail from `EntityConfig`                  |
| `AppDocumentPage`         | Full shell when you own tabs/fields yourself (settings, config editors) |
| `AppDocumentForm`         | Schema tabs → field grid                                                |
| `AppDynamicFieldRenderer` | One field → correct control (select, secret, builders, …)               |
| `AppDocumentContentShell` | Readable max-width + gutters (`wide` for dense forms)                   |
| `AppDocumentMetaRail`     | Right rail: assign, attachments, tags, share                            |
| `AppCommentsActivity`     | Comments + activity feed                                                |


```vue
<DocumentEntityDocumentView :config="entityConfigs.companies" />
```



### 3.4 Form / field widgets (reusable by design)

Usually reached via `AppDynamicFieldRenderer`, but safe to use directly:


| Component                                             | Role                        |
| ----------------------------------------------------- | --------------------------- |
| `AppSecretInput`                                      | Show/hide secret            |
| `AppColorPicker`                                      | Color presets               |
| `AppIconPicker`                                       | Icon search                 |
| `AppImageUploadField`                                 | Image → URL/data            |
| `AppFileUpload`                                       | Dropzone files              |
| `AppUppyUploader`                                     | Full Uppy dashboard         |
| `AppSortableList`                                     | Drag-reorder list           |
| `AppRichTextNote`                                     | TipTap notes                |
| `AppRolePermissionMatrix`                             | Role × doc-type permissions |
| `AppConnectionStatusCard` / `AppConnectionTestButton` | Connection UX               |




### 3.5 App chrome & confirm


| Component / API                      | Role                                             |
| ------------------------------------ | ------------------------------------------------ |
| `AppHeader` + `AppHeaderPageActions` | Sticky header actions (create, save, refresh)    |
| `AppSlidebar` / `UserMenu`           | Nav + user menu                                  |
| `AppConfirmHost` + `useConfirm()`    | App-wide confirm (`kind: 'save' | 'delete' | …`) |
| `AppAuthLocaleSwitch`                | Locale on auth layout                            |


```ts
const { confirm } = useConfirm()
const ok = await confirm({ kind: 'delete' })
if (ok) await remove(id)
```



### 3.6 Dashboard widgets


| Component               | Role                  |
| ----------------------- | --------------------- |
| `AppSummaryCard`        | KPI card              |
| `AppEchart`             | ECharts wrapper       |
| `AppEventCalendar`      | Month calendar        |
| `AppChartPeriodToolbar` | Year / period filters |


---



## 4. Shell / orchestrator (wire adapters — don’t fork lightly)

These are **reusable page patterns**, not low-level UI atoms.


| Component                                                              | Use for                                                          |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `EntityWorkspaceView`                                                  | Most Organization / User / Meeting History / Document list pages |
| `EntityDocumentView`                                                   | Matching detail/new routes                                       |
| `AppMeetingTopicBoard`                                                 | Meetings → Topic board only                                      |
| `AppRecordStageBoard`                                                  | Incoming / Outgoing / Document / Master List stage boards        |
| `AppRecordLogBoard`                                                    | Record logs                                                      |
| `AppFileUploadBoard`                                                   | Portal file upload                                               |
| `AppConfigEntityList` + `AppRecordTypeList` / `AppRecordAttributeList` | Configuration indexes                                            |
| `AppRecordTypeEditor` / `AppRecordAttributeEditor`                     | Configuration editors                                            |


**Rule:** Add a new entity to `entities.ts` and reuse Entity* first. Only add a new `App*Board` when the UX needs a left rail, drag-assign, or non-table layout.

---



## 5. Feature-specific (not global reusable)

Keep these in their domain folder. Reuse **inside** the domain; do not promote to `common/` unless a second domain needs the same API.


| Domain                     | Components                                                                                                                             |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Auth**                   | `AppAuthTermsDialog`                                                                                                                   |
| **Meeting**                | `AppMeetingBoardCard`, `AppMeetingTopicSideCard`, `AppMeetingNotesDialog`                                                              |
| **Record**                 | `AppRecordBoardCard`, `AppRecordStageSideCard`                                                                                         |
| **Configuration builders** | `AppAttributeOptionsBuilder`, `AppWorkflowStageBuilder`, `AppValidationRuleBuilder`, `AppVisibilityRuleBuilder`, `AppNumberingPreview` |
| **Settings**               | Use `AppDocumentPage` + settings schemas (no dedicated settings card kit)                                                              |


These are **valid** components — “unreusable globally” means “wrong to treat as app-wide primitives,” not “bad code.”

---

## 6. Removed prepared components (do not resurrect)

Deleted as unused duplicates of live flows:


| Removed | Use instead |
| -------- | ----------- |
| `AppFormSection` | `AppDocumentForm` sections |
| `AppStatusBadge` | Table column `cell: 'badge'` |
| `AppUnsavedChangesDialog` | `useConfirm` |
| `AppAttachmentsPanel` | `AppDocumentMetaRail` attachments |
| `AppHeaderActions` | `AppHeaderPageActions` / `useAppHeader` |
| `AppSettingCard` / `AppSettingsPlaceholder` | Settings pages via `AppDocumentPage` |
| `AppMutilSelect` | Renamed to `AppMultiSelect` |


---

## 7. Composables & utils to pair with components


| Piece                                                                | Role                                             |
| -------------------------------------------------------------------- | ------------------------------------------------ |
| `useEntityWorkspace`                                                 | URL search/filters/sort/page + table/kanban data |
| `useDocumentPage`                                                    | Load/save/dirty/comments for documents           |
| `useConfigListPage`                                                  | Config list CRUD                                 |
| `useMeetingTopicBoard` / `useRecordStageBoard` / `useRecordLogBoard` | Board state                                      |
| `useAppHeader`                                                       | Title, breadcrumbs, badges, actions              |
| `useConfirm`                                                         | Modal confirms                                   |
| `useFilterAutoWidth`                                                 | Filter trigger width grows with label            |
| `utils/filter/menu-items.ts`                                         | Normalize select options                         |
| `utils/filter/select-ui.ts`                                          | Active/idle filter chrome                        |
| `utils/field-help.ts`                                                | Field helper text keys                           |
| `utils/object-path.ts`                                               | Nested document field get/set                    |


---



## 8. How to add features the reusable way



### New list + detail entity (table/kanban)

1. Add `EntityConfig` in `app/config/entities.ts` (columns, filters, document tabs, permissions).
2. Create thin pages:

```vue
<!-- pages/organizations/foo/index.vue -->
<template>
  <WorkspaceEntityWorkspaceView :config="entityConfigs.foo" />
</template>
```

```vue
<!-- pages/organizations/foo/[id].vue -->
<template>
  <DocumentEntityDocumentView :config="entityConfigs.foo" />
</template>
```

1. Wire mock/API adapter; do **not** clone toolbar/table.



### New filter on an existing workspace

1. Add `FilterDef` on the entity config (`type: 'select' | 'multiselect'`).
2. `AppWorkspaceToolbar` + `AppFilterSelect` pick it up automatically.
3. Ensure adapter query understands the filter key.



### New field type on documents

1. Extend field schema type.
2. Render in `AppDynamicFieldRenderer` (reuse or add one `common/` control).
3. Add i18n label + `fieldHelp` if needed.



### New board-style page

1. Compose `AppWorkspacePage` + `AppLiveSearch` / `AppInputDateRange` + domain cards.
2. Put state in `composables/<domain>/use…`.
3. Keep cards in `components/<domain>/`.

---



## 9. High-performance patterns (this codebase)



### 9.1 Prefer server / mock paging over client filtering huge lists

- `AppServerTable` + workspace composable already page/sort/filter via query.
- Do not load entire datasets into the client to filter locally (see product UI map).



### 9.2 Keep reactivity cheap

```ts
// Good: derive only what the template needs
const rows = computed(() => store.pageItems)

// Avoid: deep clone on every keystroke
// structuredClone(vueProxy)  — prefer plain objects / toRaw when snapshotting
```

- Don’t put **functions** in `useState` for header actions (use `AppHeaderPageActions` / header API as today).
- Prefer `computed` over manual `ref` sync for derived labels/counts.



### 9.3 Lists and boards

- Use stable `:key="row.id"` (never array index for mutable lists).
- Kanban: columns grow; **board host** scrolls on Y — don’t nest competing scroll containers.
- Virtualize only when a single column is huge; current boards use bounded “load more.”



### 9.4 Filters & search

- Debounce search in the workspace composable / URL sync (toolbar binds `v-model` to that state).
- Reuse `getFilterSelectUi` / `AppLiveSearch` so style and active state stay consistent without per-page CSS.
- **Cmd+K global search** (`layouts/default.vue` + `useGlobalSearch`): keyword (default) / semantic modes over the Phase 2 localStorage file-text index (`utils/search/*` + `adapters/search.ts`), permission-filtered hits with source links, and Ask AI only on explicit click. Keep page-level `AppLiveSearch` for local list filters — do not replace it with Cmd+K.



### 9.5 Forms & documents

- One `fieldValue` / `setFieldValue` path (object-path helpers) — avoid duplicating form models.
- Textareas: keep autoresize bounded (`min` / `max` rows) to limit layout thrash.
- Heavy editors (`AppRichTextNote`, Uppy): mount when the tab/dialog is open, not on every page load if avoidable.



### 9.6 Confirms & navigation

- Use `useConfirm` instead of mounting many dialogs.
- Dirty navigation already coordinated through document composable + confirm — don’t add parallel leave guards.



### 9.7 i18n & renders

- Use `t()` / message keys; don’t recompute large option lists without `computed`.
- Badge/cell renderers in table column defs stay pure and cheap.



### 9.8 Component API hygiene (reusable + fast)

```ts
// Good reusable API
defineProps<{ items: Array<{ label: string, value: string }> }>()
const model = defineModel<string | null>()

// Bad: pulls whole entity config into a “common” button
defineProps<{ department: Department; currentUser: User; permissions: ... }>()
```

- Prefer `defineModel` for v-model.
- Emit serializable payloads (`id`, `key`), not giant reactive graphs.
- Mark pure display bits with clear props; avoid hidden global store reads inside deep presentational components when props suffice.

---



## 10. Checklist before creating a new component

1. Does `EntityWorkspaceView` / `EntityDocumentView` already cover it?
2. Is there already something in `common/` or `workspace/`?
3. Will a **second** feature need this exact API within ~1–2 iterations?
  - **No** → keep under `meeting|record|configuration|portal|settings|auth`.
  - **Yes** → put in `common/` or `workspace/` with generic props.
4. Can styling share `utils/filter/select-ui` or Nuxt UI `ui` slots instead of one-off CSS?
5. Is data paged/filtered on the server (or mock query layer), not in the template?

---



## 11. Summary map

```text
REUSE EVERYWHERE
  AppLiveSearch, AppFilterSelect, AppMultiSelect, AppSingleFilterSelect
  AppInputDate*, AppWorkspaceToolbar
  AppServerTable, AppRowActionsMenu, AppWorkspacePage
  AppDocumentPage stack, AppDynamicFieldRenderer, AppDocumentContentShell
  useConfirm, useAppHeader, select-ui helpers

REUSE VIA CONFIG
  EntityWorkspaceView, EntityDocumentView, entityConfigs.*

REUSE IN DOMAIN ONLY
  Meeting/Record cards & boards, config builders, auth terms

ORCHESTRATORS (extend carefully)
  App*Board, AppConfig*List/Editor

AVOID NEW COPIES OF
  Search/filter/sort chrome, confirm dialogs, header action wiring,
  table row action menus, document field switches
```

---

*Generated for the Docetra Nuxt frontend. Update this file when you add a shared component or change the Entity* contracts.*