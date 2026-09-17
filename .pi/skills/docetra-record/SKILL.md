# docetra-record

## Purpose

Use when implementing or modifying records, record types, record stages, dynamic attributes, record attachments, record-organization links, record history, or the meeting board/topic-container behavior.

## Source Documents

- docs/specification/modules/record.md
- docs/specification/modules/storage-integration.md (three-layer attachment architecture, referenced by record.md)

## Domain Overview

The record module is the core business module of Docetra v2. It manages a unified record model: creation, updates, type-driven behavior, workflow stage tracking, dynamic attributes, history/timeline, and relationships to other records, organizations, and files. Presentation is configuration-driven — never hardcoded per screen.

## Key Entities

| Entity | Responsibility |
|---|---|
| Record | Primary operational entity; a business item tracked through its lifecycle |
| Record type | Defines behavior, attribute set, and workflow structure of a record |
| Record stage | Current phase of a workflow for a record type |
| Record detail | Typed dynamic values for record-specific fields |
| Record attachment | Links a record to a file or another related record |
| Record organization | Links a record to one or more organizations with a defined relationship role |
| Record stage template | Stage structure for a record type |
| Record time | Configurable timeline field chosen from a priority list (enum/metadata config), using the first valid candidate field |

## Relationships

- Record → Record type (behavior + validation).
- Record → Record detail (dynamic attribute values).
- Record → Record (record-to-record links, when business logic requires).
- Record → Organization via record_organization (ownership, participation, review, visibility).
- Record → File via record_attachment (three-layer: storage file → file metadata → record-attachment link).
- Meeting is a special record type: behaves like a normal stage-based record AND acts as a topic container.

## Business Rules

- Record behavior MUST be type-driven, not hardcoded per screen.
- Stage transitions MUST be valid for the record type.
- History MUST be preserved for important record changes.
- Dynamic attributes MUST be read from record type metadata and persisted in a structured format.
- `record_time` MUST be resolved from a configurable priority list (enum/metadata), using the first valid candidate field; it MUST be indexed; mixed timelines without a specific record type sort by `record_time`.
- The record module MUST NOT own access policy; it consumes centralized access services from people_access.
- Attachments use three layers: storage file (binary in object storage), file metadata (PostgreSQL record: name, path, size, mime type, storage type, direct URL, status), record-attachment link (business linkage). Storage concerns stay independent from business linkage.
- URL attachments follow the same three-layer pattern but SKIP upload — a file metadata record represents the URL and a record-attachment link connects it to the record; the business link exists even with no binary file.
- Presentation rules: every record type gets a dedicated slug-based page route; list AND board views where stage-based workflow is supported; board groups by stage with drag-and-drop between stages; cards/rows show summary + important info for scanning; create flow is lightweight (essential fields only); detail page supports editing, related records, files, history/activity, permissions, reminders/notifications.

## Implemented Record Surfaces (verified in code)

Backend `TYPE_UI_DEFAULTS` (backend/app/modules/record/domain/map.py) auto-seeds built-in types via `resolve_or_ensure_type`:

| Type code | Route | uiSurface |
|---|---|---|
| meeting_topic | /meetings/topics | meeting |
| meeting_history | /meetings/history | meeting |
| document | /records/documents | document |
| incoming_document | /records/incoming-documents | document |
| outgoing_document | /records/outgoing-documents | document |
| master_list_request | — | document |

Menus/routes derive from active record types + `uiSurface` (useRecordSurfaces); dynamic routes `/records/{typeCode}` and `/meetings/{typeCode}` resolve by code, slug, or routeBase suffix.

### Topic container behavior (frontend: useMeetingTopicBoard.ts, AppMeetingTopicBoard.vue)

- Create topic (title, description, status active); update with concurrency `version`; archive/activate. Deleting a topic detaches child meetings server-side (`parent_record` + `topicId` details cleared → children appear in Unassigned pool).
- Assign meeting → topic via drag (`topicId`, `topicTitle`, `sortOrder`); drop on Unassigned row → `topicId: null` (backend query `topicId: '__empty__'`). **Backend validates topics**: nonexistent/wrong-type → 404/422, archived → 422.
- Meetings per topic: paginated (limit 20), search `q`, date range, `excludeStage` completed; pool views sort by `meetingDate`, topic views by `sortOrder`.
- Reorder via `reorderMeetingsInTopic({ topicId, orderedMeetingIds })`.
- Rail counts from `getGroupCounts('topicId')` → `{ total, unassigned, groups }`.
- Create meeting inside topic: navigate `/meetings/history/new?returnTo=/meetings/topics&topicId=...`.
- Complete meeting → transition to completed stage → removed from board ("moved to history"), retained in /meetings/history.

### Document flows (verified in config/entities.ts)

- `incomingDocuments` (incoming_document): reference number, title, senderOrganization, receivedDate, owner, assignee, waiting; tabs on documentType/receivedDate.
- `outgoingDocuments` (outgoing_document): same model, sentDate.
- `documents` (document): combined all-documents view at /records/documents — reference number, title, recordTypeName, documentDate, updatedAt.
- Stage/step management via workflow stage board (drag between stages); stages configured per type in Configuration (workflow stage builder).

### Record logs

- /records/logs (+ [id]) via AppRecordLogBoard + useRecordLogBoard; activities + comments tables; document shell includes AppCommentsActivity.

### Meeting participant/organization fields

- Meetings and documents attach officers (`participants`, `involvedOfficers` — officer @mention), departments (`internalUnits` — department @mention), companies (`externalUnits`, `senderOrganization`).

## Meeting Board Rules

- Meetings on the standalone board/list follow normal stage-based behavior (create, update, move through stages).
- Dragging a meeting into a meeting-topic container MUST remove it from the standalone view (no duplicate visual records).
- The topic container acts as a parent card showing child meetings in a vertical list following the CONFIGURED ordering rule — never a fixed hardcoded order.
- Topic containers SHOULD show child count or summary info on the parent card.
- The meeting area MUST support both workflow-board and topic-grouping views.

## Record Lifecycle

1. Create → 2. Classify by record type → 3. Set initial stage/status → 4. Add details and relationships → 5. Update through workflow → 6. Preserve history → 7. Retain for search and review.

No other state machine is defined. Exact stage names per record type: `Needs verification` (driven by record_stage_template configuration).

## API Rules

The module SHOULD expose APIs for:

- Record: list, detail, create, update.
- History retrieval.
- Linked record retrieval.
- Attachment association.
- Stage/status movement.
- Search and filtering.

Record creation requires: record type, title, owning context, initial status, initial stage (where applicable), dynamic fields, optional attachments/references.

Exact routes/payloads: `Needs verification`.

## Data Rules

Module owns or primarily manages: `record`, `record_detail`, `record_attachment`, `record_organization`, `record_stage_template`, `record_type`, `record_attribute`, `record_template`.

`Specification conflict:` `record_type`, `record_attribute`, and `record_template` are also claimed by admin-config.md under its "Data ownership". Do not silently pick an owner; confirm with the user. The dependency boundary ("record may depend on admin_config for types and attributes") suggests admin_config defines them, but this is not explicitly resolved.

## Validation Rules

- Record type MUST be present and valid.
- Required attributes (per type) MUST be present.
- Stage transitions MUST be valid.
- Organization linkage MUST be valid.
- User MUST have permission to create/edit the record.
- Record state changes MUST be allowed for the current type.

## Edge Cases

- Moving a record to a stage not defined in its type's stage template → reject. (Derived from specification: "stage transitions are valid".)
- URL attachment with no binary → still creates file metadata + attachment link, just skips upload. (Explicit in spec.)
- Meeting dragged into topic container while another user views the standalone board → meeting appears only inside the container. (Explicit in spec.)
- Mixed-type timeline view → sort by indexed `record_time`, resolved per-type from priority config. (Explicit in spec.)

## Implementation Guidance

- Drive all screens from record type configuration; never hardcode per-slug behavior.
- Keep search-friendly fields indexed and normalized.
- Consume storage_integration for file linkage; do not implement storage internals here.
- Consume people_access access services; do not implement permission policy here.
- Keep workflow rules explicit and testable; preserve timeline-friendly history.

## DO NOT

- DO NOT own or implement access policy in this module.
- DO NOT hardcode stage orders or meeting child ordering.
- DO NOT store binary file content in the record module.
- DO NOT create duplicate visual entries for meetings (standalone + container simultaneously).
- DO NOT break the three-layer attachment separation (binary / metadata / link).
- DO NOT skip history on important record changes.

## Testing Checklist

- [ ] Record can be created with type, title, owning context, initial status/stage, dynamic fields.
- [ ] Missing record type is rejected.
- [ ] Missing required attribute (per type config) is rejected.
- [ ] Invalid stage transition is rejected.
- [ ] Invalid organization link is rejected.
- [ ] Unauthorized user cannot create/edit.
- [ ] History is preserved for important changes.
- [ ] `record_time` resolves via priority list and is indexed; mixed timeline sorts by it.
- [ ] List + board views render from type configuration; board drag-and-drop changes stage.
- [ ] Meeting appears on standalone board; dragging into topic container removes it from standalone view.
- [ ] Topic container lists children in configured order with child count/summary.
- [ ] File attachment creates metadata + link; URL attachment skips upload but still links.

## Needs Verification

- Canonical owner of record_type / record_attribute / record_template (conflict with admin-config.md).
- Exact status values and stage template shape.
- Exact permission checks consumed from people_access.
- Exact API contracts.
- Configuration format of the meeting child ordering rule and the `record_time` priority list.
