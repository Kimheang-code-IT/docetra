# Docetra v2 — Product Features (Frontend-Verified Reference)

This document records the implemented product behavior, verified against the current frontend and backend. It is the practical companion to the module specifications. Where a behavior is verified in code it is marked **[verified]**; anything not yet verified at runtime is marked **Needs verification**.

Routes use the `/api/v2` prefix on the backend. Frontend paths are Nuxt routes under `frontend/app/pages`.

---

## 1. Record surfaces (type-driven navigation)

The system is driven by **record types**. Each active record type has a `uiSurface`, a `slug`, and a `routeBase`; menus and dynamic routes are generated from them — never hardcoded per screen. **[verified]** (`backend/app/modules/record/domain/map.py` `TYPE_UI_DEFAULTS`, `frontend/app/composables/record/useRecordSurfaces.ts`)

Built-in record types:

| Type code | Slug / route | uiSurface | Purpose |
|---|---|---|---|
| `meeting_topic` | `/meetings/topics` | meeting | Topic containers that group meetings |
| `meeting_history` | `/meetings/history` | meeting | Meeting records (stage-based) |
| `document` | `/records/documents` | document | General/combined document type |
| `incoming_document` | `/records/incoming-documents` | document | Incoming document tracking |
| `outgoing_document` | `/records/outgoing-documents` | document | Outgoing document tracking |
| `master_list_request` | — | document | Master list requests |

- Routes: `/meetings/{typeCode}` and `/records/{typeCode}` (list/board), `/records/{typeCode}/new`, `/records/{typeCode}/{id}` (detail).
- Views: table list and kanban stage board per record type (`views: ['table','kanban']`).
- `resolve_or_ensure_type` auto-seeds built-in types with UI defaults. **[verified]**

## 2. Meetings and topic containers

Implemented in `frontend/app/composables/meeting/useMeetingTopicBoard.ts`, `frontend/app/components/meeting/AppMeetingTopicBoard.vue`. **[verified]**

- **Topic rail**: topics list with search, pagination, active/archived topics shown (so Activate stays available).
- **Create topic**: dialog creates a topic (`title`, `description`, `status: active`).
- **Update topic**: title/description edit with optimistic concurrency (`version` / `If-Match`).
- **Archive/activate topic** (`setTopicActive`).
- **Assign/unassign meeting to topic**: drag a meeting card onto a topic (`assignMeetingToTopic` with `topicId`, `topicTitle`, `sortOrder`); drop onto **Unassigned** row sets `topicId: null`. Assigning to an inactive topic is rejected with a toast.
- **Unassigned pool**: `__unassigned__` sentinel row; backend query uses `topicId: '__empty__'`.
- **Meetings per topic**: paginated list (default limit 20) with search (`q`) and date-range filters (`startDate`, `endDate`); completed-stage meetings are excluded from the board (`excludeStage`).
- **Ordering**: `sortOrder` inside a topic; `reorderMeetingsInTopic` persists `orderedMeetingIds`. Pool views sort by `meetingDate`; topic views sort by `sortOrder`.
- **Count summary**: `getGroupCounts('topicId', ...)` returns `{ total, unassigned, groups }` for rail badges.
- **Create meeting inside a topic**: `openCreateMeeting` carries `returnTo` and `topicId` query params to `/meetings/history/new`.
- **Complete meeting**: `completeMeeting` transitions the meeting to the completed stage; it disappears from the board ("moved to history") and remains available in `/meetings/history`. **[verified]** Exact history listing filters: **Needs verification** (runtime).
- **Meeting fields** (`meetingHistory` entity): letter number, subject, letter date, meeting date (datetime), duration, mode (online/offline/hybrid), meeting URL, location, **participants** (officer @mention), **internalUnits** (department @mention), **externalUnits** (company @mention), tags, topic select.
- **Drive file picker**: `AppMeetingDriveFilePicker` links Drive files to a meeting.

## 3. Document flows (incoming / outgoing / combined)

Entity configs in `frontend/app/config/entities.ts` (`incomingDocuments`, `outgoingDocuments`, `documents`). **[verified]**

- **Incoming documents** (`/records/incoming-documents`): columns include reference number, title, sender organization (`senderOrganization.name`), received date, owner, assignee, waiting; date filter on `receivedDate`; tabs for `documentType` / dates.
- **Outgoing documents** (`/records/outgoing-documents`): same management model with `sentDate` tab date key.
- **Combined documents** (`/records/documents`, record type `document`): single list/table combining documents; columns: reference number, title, record type name, document date, updated at; date filter; document tabs. This is the "all documents together" view.
- **Tracking / step management**: stage-based workflow via `recordWorkflowStages` (e.g. `waiting_related_document` stage exists) and the kanban stage board (`AppRecordStageBoard`, drag between stages). Stage set per record type via the workflow stage builder in Configuration. **[verified]** (components); per-type default stage lists for documents: **Needs verification**.
- **Create/edit** uses the shared `DocumentEntityDocumentView` + `useDocumentPage` shell with dynamic field rendering (`AppDynamicFieldRenderer`) driven by record-type attribute configuration.
- Document create/edit supports company + organization selects and officer @mentions (participants/internal/external units) per `config/entities.ts` line 104 comment. **[verified]**

## 4. Record logs / history

- Pages: `frontend/app/pages/records/logs/index.vue`, `[id].vue`; component `AppRecordLogBoard`; composable `useRecordLogBoard`. **[verified]**
- Records keep activity/history (backend `activities` + `comments` tables; `AppCommentsActivity` on the document shell).
- System-level logs: `/system-monitor/system-logs`. Portal logs: `/portal/portal-logs`.

## 5. Departments (organizations)

- Pages: `/organizations/departments` (+ new/[id]); entity key `departments`; permission `organizations.departments.view`. **[verified]**
- Backend `organization` model supports parent-child hierarchy (main department → sub-departments); hierarchy updates are validated cycle-safe per `docs/specification/modules/organization.md`. **[verified]** (model has parent); cycle validation runtime behavior: **Needs verification**.
- Departments are selectable via @mention (`Type @ or a department name ...`) when creating meetings and documents (`internalUnits`).

## 6. Companies

- Pages: `/organizations/companies` (+ new/[id]); entity with `orgType` dynamic routes `/organizations/[orgType]`. **[verified]**
- Companies attach to meetings/records via `externalUnits` / `senderOrganization` selects.
- **Sector** (`/sector`) and **Purpose** (`/purpose`) are reusable classification forms; company forms select from them. **[verified]** (pages + org select tabs); option source endpoints: **Needs verification**.

## 7. Officers

- Pages: `/officers` (+ new/[id]); permission `organizations.officers.view`. **[verified]**
- Officers are attached as **participants** to meetings and documents via officer @mention selects (`involvedOfficers`, `participants`).
- Officer↔user mapping exists in user management (entity `officerId` select with help text). **[verified]**

## 8. Portal (files & Google Drive)

- **File upload**: `/portal/file-upload` (+ [id]); `AppFileUploadBoard`. **[verified]**
- **Google Drive sync**: `/portal/google-drive-sync` (+ new/[id]); `AppGoogleDriveSync`; create source, start sync, poll job, refresh files. **[verified]** (pages exist); job polling behavior: **Needs verification** (runtime).
- **Portal logs**: `/portal/portal-logs` (+ [id]).

## 9. Users, roles, permissions

- Pages: `/user-management/users` (+ new/[id]) and `/user-management/roles` (+ new/[id]). **[verified]**
- User form maps to an officer (`officerId`); roles use the dynamic permission catalog (`repositories/contracts/permission-catalog.ts`).
- Permission gating is presentation-only (`auth.canAccessPage(config.permission)`); backend authorization is authoritative.

## 10. Configuration (record types, attributes, settings)

- **Record types**: `/configuration/record-types` (+ new/[id]); `AppRecordTypeEditor`, `AppRecordTypeList`, `AppWorkflowStageBuilder`, `AppValidationRuleBuilder`, `AppVisibilityRuleBuilder`, `AppNumberingPreview`. Dynamic fields/steps per record type are configured here. **[verified]**
- **Attribute catalog**: `/configuration/record-attributes` (+ new/[id]); `AppRecordAttributeEditor`, `AppAttributeOptionsBuilder`. Attributes are a reusable catalog mapped to record types via record templates (backend `record_attribute` + `record_template`). **[verified]** (backend models).
- **Record type logs**: `/configuration` discussion/list composables (`useConfigListPage`, `useConfigurationDiscussion`). **[verified]** (files exist); exact behavior: **Needs verification**.
- **Settings**: `/settings/app-config`, `/settings/app-info`, `/settings/storage`; composables `useAppBranding`, `useAppLocalization`, `useAppRuntimeConfig`, `useCardFields`.

## 11. Archive

- `/archive` uses `ArchiveWorkspaceView` + `useArchiveWorkspace` across sources: `meetingTopics`, `meetingHistory`, `incomingDocuments`, `outgoingDocuments`, `documents`, `masterListRequests`; supports restore (with concurrency token), permission-filtered source options, "All types" combined view. **[verified]**

---

## Cross-cutting rules (restate)

- All HTTP via repositories/adapters + `useApi()`; no direct `$fetch` in components.
- New user-facing text requires English + Khmer i18n (`i18n/`).
- Optimistic concurrency via `version` + `If-Match` (`withConcurrencyToken`).
- Backend authorization authoritative; frontend permissions are UX gating only.
- Menus/routes derive from active record types + `uiSurface`.
