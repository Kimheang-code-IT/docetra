# Prompt 00A — Reusable Nuxt UI Workspace and Document Components

## Copy/paste prompt

Build the shared Docetra workspace and ERP-style document-page component system in the existing Nuxt 4, Vue 3, TypeScript, Nuxt UI 4, Pinia, i18n, VueUse, and TanStack Vue Table application. Inspect and reuse compatible components already present in `frontend/app/components`.

Use Nuxt UI primitives for the complete interface. Do not add another UI framework and do not copy ERPNext code or branding. Components must be typed, accessible, responsive, permission-aware, and API-agnostic.

## Workspace components

### `AppWorkspacePage`

Provide breadcrumb, localized title/description, result count, primary create action, overflow actions, sticky toolbar, and content slot. The create action navigates to the entity’s `/new` route.

### `AppWorkspaceToolbar`

Provide debounced search, filters, active-filter chips, date range, sort, column visibility, refresh, export, and table/Kanban toggle. Synchronize supported state with URL query parameters.

### `AppServerTable`

Generalize existing table primitives around TanStack Vue Table. Support server pagination, sorting, filtering, selection, sticky header, column visibility, row actions, bulk actions, skeletons, empty/error states, and responsive priority columns. Row activation navigates to the canonical document route.

### `AppKanbanBoard`

Render typed workflow stages as horizontal columns with counts, bounded cards, per-column loading, and “Load more”. Support pointer and keyboard movement, validated transitions, optimistic updates with rollback, conflict feedback, and an accessible “Move to stage” action. Card activation navigates to the canonical document route.

## Document-page components

### `AppDocumentPage`

Create the reusable full-page shell for new, detail, and edit routes. Compose it from Nuxt UI primitives such as `UPage`, `UPageHeader`, `UBreadcrumb`, `UTabs`, `UForm`, `UFormField`, `UButton`, `UBadge`, `UDropdownMenu`, `UCard`, `USeparator`, `USkeleton`, and responsive layout utilities available in the installed version.

Provide:

- Sticky document header with breadcrumb, title, status, previous/next, overflow menu, and Save.
- Schema-driven tabs and sections.
- Main content column plus right metadata rail.
- Read, edit, loading, not-found, error, conflict, and permission-denied states.
- Unsaved-change protection for route navigation and browser close.
- Focus on the first invalid field after validation failure.
- Canonical navigation from `/new` to `/:id` after successful creation.

### `AppDocumentForm`

Render schema-driven sections using responsive one- or two-column grids. Support section title, help text, visibility rules, read-only state, validation, dependent fields, and server validation error mapping. Avoid a single extremely long unstructured form.

### `AppDynamicFieldRenderer`

Render text, textarea, number, date, date-time, select, multi-select, boolean, organization, officer, record relation, file, and URL fields using Nuxt UI form controls. Keep values typed and accessible.

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

### `AppAttachmentsPanel`

Support files and URL attachments using storage metadata plus record-attachment links. Include upload progress, retry, safe preview/download, association state, and permissions. Do not store binary content in Pinia.

### `useEntityWorkspace`

Coordinate workspace URL state, table/board mode, search, filters, sorting, pagination/cursors, refresh, request cancellation, and optimistic board transitions. Accept typed adapters instead of hardcoded endpoints.

### `useDocumentPage`

Coordinate route identity, create/read/edit state, schema, initial values, dirty tracking, validation, save, conflict handling, lazy tab data, comments, activity, permissions, and previous/next navigation. Accept entity adapters and do not invent endpoints inside UI components.

## Shared interaction contract

- Add navigates to `/module/entity/new`.
- A table row or Kanban card navigates to `/module/entity/:id`.
- Save stays on the document page and refreshes only affected data.
- Successful creation replaces `/new` with the canonical ID route.
- Cancel or Back returns to the preserved workspace URL when safe.
- Unsaved changes require confirmation.
- Previous/next respects the source workspace ordering where available.
- Backend authorization is authoritative; frontend permission checks control visibility only.

## Acceptance

Add focused tests for URL state, pagination, stage rollback, document routing, unsaved changes, validation focus, create-to-detail navigation, comment submission, and activity rendering. Run typecheck and production build. Demonstrate the shared system on at least one workflow record page before migrating the remaining page prompts.
