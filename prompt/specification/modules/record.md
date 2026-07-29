# Docetra v2 Module: Record

## Purpose

The record module is the core business module of Docetra v2. It manages the unified record model, record history, workflow stage tracking, dynamic attributes, attachments, and relationships between records and organizations.

## Module responsibilities

The record module owns:
- unified record creation and updates.
- record type behavior.
- record status and stage.
- record history and timeline data.
- dynamic record attributes.
- record-to-record relationships.
- record-to-organization relationships.
- record attachment relationships.
- record search support for record-specific fields.

## Core concepts

### Record
A record is the primary operational entity in the system. It represents a business item that must be tracked through its lifecycle.

### Record type
A record type defines the behavior, attribute set, and workflow structure of a record.

### Record stage
A stage describes the current phase of a workflow for a record type.

### Record detail
Record detail stores typed dynamic values for record-specific fields.

### Record attachment
Record attachment links a record to a file or another related record when required.

### Record organization link
Record organization links a record to one or more organizations with a defined relationship role.

## Presentation and screen model

Each record type gets its own slug-based page. That page can show either a list view or a board view, and the shared interaction model is stage-based grouping with drag-and-drop. Cards and list rows should always show summary and other important info so users can scan records quickly without opening detail pages.

The detail page is where richer management happens. It should include the summary, full details, related records, files, activity and history, permissions, and reminders or notifications. The create flow stays lightweight, while the detail page handles richer editing and operational follow-up.

### Key rules

- Each record type must have a dedicated page route based on its slug.
- List view and board view must both be available where the record type supports stage-based workflow.
- Board view must group records by stage and support drag-and-drop to move records between stages.
- Card and row rendering must show summary fields and other important info for quick scanning.
- The create flow must be lightweight and capture only essential fields.
- The detail page must support editing, viewing related records, managing files, reviewing history, and checking permissions.
- The presentation model must be driven by record type configuration, not hardcoded per screen.

## Functional behavior

### Record creation
The module must support creation of records with:
- record type.
- title.
- owning context.
- initial status.
- initial stage where applicable.
- dynamic fields.
- optional attachments or references.

### Record update
The module must support editing records according to access rules and record type validation.

### Workflow movement
The module must support stage and status updates for workflow-enabled record types.

### History tracking
The module must preserve history for important record changes.

### Dynamic attributes
The module must read attribute configuration from record type metadata and persist values in a structured format.

### Record time resolution
`record_time` is configurable rather than fixed to one column. The system chooses it from a priority list stored in enum or metadata configuration, using the first valid candidate field. When users view a mixed timeline without a specific record type, the system sorts by `record_time`. This field should be indexed for performance.

### Record linking
The module must support links to other records when business logic requires it.

### Attachment and link behavior
Attachments are separated into three layers: storage file, file metadata, and record-attachment link. That keeps storage concerns independent from business linkage. URL attachments follow the same pattern but skip upload, because the business record still needs a link even when there is no binary file. The record module consumes this structure through the storage integration module.

### Organization association
The module must allow records to reference organizations for ownership, participation, review, or visibility.

## Meeting board behavior

Meeting is a special record type. It still behaves like a normal stage-based record on its own page, so it can appear in list or board view and move through its own workflow stages.

### Standalone meeting board

On the standalone meeting board or list, meetings are displayed as normal stage-based records. They can be created, updated, and moved through stages like any other record type.

### Meeting-topic container

A meeting can be dragged into a meeting-topic container. Once it is linked there, it is removed from the standalone meeting board or list and shown only inside the topic container. This avoids duplicate visual records and keeps the board clean.

### Child meeting display

The meeting-topic container acts like a parent card. It shows its child meetings in a vertical list, and that list follows the configured ordering rule rather than a fixed hardcoded order. That makes the meeting area both a workflow board and a topic grouping view at the same time.

### Key rules

- Meetings on the standalone board must follow normal stage-based behavior.
- Dragging a meeting into a meeting-topic container must remove it from the standalone view.
- The meeting-topic container must display child meetings in a configured order.
- The meeting area must support both workflow board and topic grouping views.
- Meeting-topic containers should show child count or summary info on the parent card.

## Record lifecycle expectations

A record should generally move through the following lifecycle:
1. Create.
2. Classify by record type.
3. Set initial stage or status.
4. Add details and relationships.
5. Update through workflow.
6. Preserve history.
7. Retain for search and review.

## Key validations

The module should validate:
- record type is present and valid.
- required attributes are present.
- stage transitions are valid.
- organization linkage is valid.
- user has permission to create or edit the record.
- record state changes are allowed for the current type.

## Data ownership

The record module should own or primarily manage:
- `record`
- `record_detail`
- `record_attachment`
- `record_organization`
- `record_stage_template`
- `record_type`
- `record_attribute`
- `record_template`

## API responsibilities

The module should expose APIs for:
- record list.
- record detail.
- record create.
- record update.
- history retrieval.
- linked record retrieval.
- attachment association.
- stage/status movement.
- search and filtering.

## Dependency boundaries

The record module may depend on:
- people_access for permissions and identity context.
- organization for organization references.
- storage_integration for file linkage.
- admin_config for types and attributes.

The record module should not own access policy itself; it should consume centralized access services.

## Search and reporting support

The module should make record data available for:
- global search.
- operational dashboards.
- future reporting models.

Search-friendly fields should be kept indexed and normalized where appropriate.

## Implementation notes

- Keep record behavior type-driven rather than hardcoded per screen.
- Use configuration-driven attributes for flexibility.
- Preserve timeline-friendly history.
- Avoid placing unrelated business logic in this module.
- Keep workflow rules explicit and testable.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `02-domain-model.md`
- `03-functional-requirements.md`
- `04-permissions-and-access.md`
- `07-data-model.md`
- `modules/organization.md`
- `modules/storage-integration.md`
- `modules/admin-config.md`
