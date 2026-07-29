# Docetra v2 User Flows

## Purpose

This document defines the primary user flows for Docetra v2. It describes how users should move through the system for the most important operational tasks.

## Flow design principles

- Keep flows simple and predictable.
- Use record-type-specific screens only where needed.
- Preserve traceability in every major workflow.
- Ensure permission checks happen before action execution.
- Keep internal and external user flows separate where access differs.

## Record screen model

Each record type gets its own slug-based page. That page can show either a list view or a board view, and the shared interaction model is stage-based grouping with drag-and-drop. Cards and list rows should always show summary and other important info so users can scan records quickly without opening detail pages.

The detail page is where richer management happens. It should include the summary, full details, related records, files, activity and history, permissions, and reminders or notifications. The create flow stays lightweight, while the detail page handles richer editing and operational follow-up.

This screen model applies consistently across all record-type flows. The presentation is driven by record type configuration, not hardcoded per screen.

## Main flow categories

- Authentication and session access.
- Dashboard and operational overview.
- Record creation and editing.
- Record lifecycle movement.
- Meeting management.
- Organization management.
- File upload and attachment handling.
- Search and retrieval.
- Configuration and administration.
- External company access.

## Authentication flow

1. User opens the application.
2. User signs in through the authentication provider.
3. Backend validates the session and resolves the linked user context.
4. System loads the user’s role, department, and access scope.
5. User is redirected to the dashboard or landing page allowed by their role.

If the user has no valid access, the system must deny entry cleanly.

## Dashboard flow

1. User lands on the dashboard after sign-in.
2. System shows operational summary data based on the user’s access scope.
3. User can navigate into active records, pending work, or recent history.
4. Dashboard widgets should reflect record type, stage, and status.

## Record creation flow

1. User selects a record type.
2. System loads the required attributes and form structure.
3. User enters the record data.
4. Backend validates the payload and access rights.
5. Record is saved with its type, ownership context, and initial status.
6. The system creates the initial history entry.
7. User is redirected to the record detail page.

## Record edit flow

1. User opens an existing record.
2. System checks view or edit permission.
3. User updates allowed fields.
4. Backend validates the changes.
5. Changes are saved.
6. History and audit records are updated.
7. User returns to the record detail page or list view.

## Record lifecycle flow

1. User opens a record in a workflow-enabled type.
2. User changes stage, status, or related workflow state.
3. Backend validates the transition.
4. Record history and audit entries are created.
5. UI updates current stage and waiting state.

The exact transition rules may differ by record type.

## Meeting flow

1. User creates a meeting record.
2. Meeting appears on the standalone meeting board in list or board view, grouped by stage.
3. User can move the meeting through workflow stages via drag-and-drop on the board.
4. User optionally adds meeting topics as linked records or structured sub-items.
5. A meeting can be dragged into a meeting-topic container. Once linked there, it is removed from the standalone board or list and shown only inside the topic container.
6. The meeting-topic container displays its child meetings in a vertical list following the configured ordering rule.
7. Completed or finalized meetings move into history view.
8. Meeting history remains available for review.

## Document flow

1. User creates or receives a document record.
2. Document is categorized by type and workflow direction if required.
3. User tracks current stage and waiting state.
4. Document can be updated as it moves through the workflow.
5. Timeline history shows its progression.

## Organization flow

1. User opens the organization module.
2. User creates or edits an organization.
3. System validates hierarchy, sector, purpose, and contact fields.
4. Changes are saved.
5. Organization history is recorded.
6. Related records can reflect the updated organization context.

## File upload flow

1. User opens the upload interface.
2. User selects a file.
3. Backend stores the binary in object storage.
4. File metadata is saved in the database.
5. Optional record linkage is created.
6. The user sees the uploaded file attached or listed as available.

## Search flow

1. User enters a search term or filter.
2. Backend applies access-aware search constraints.
3. Results are returned based on record type, organization, status, and other indexed fields.
4. User opens the result detail page.

## Configuration flow

1. Authorized user opens the configuration area.
2. User manages record types, record attributes, document types, or settings.
3. Backend validates configuration changes.
4. The system records audit entries for the change.
5. Related record behavior updates according to the new configuration.

## External company flow

1. External user signs in.
2. System resolves the company context.
3. User sees only shared records and allowed resources.
4. User can view related records and possibly perform limited actions.
5. System blocks any action outside the external scope.

## Error and denial flow

1. User attempts an action without permission or with invalid data.
2. Backend returns a clear error response.
3. UI presents a simple and actionable message.
4. The system does not expose internal implementation details.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `02-domain-model.md`
- `03-functional-requirements.md`
- `04-permissions-and-access.md`
- `06-api-contracts.md`
- `07-data-model.md`
