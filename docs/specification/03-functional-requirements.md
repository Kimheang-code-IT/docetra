# Docetra v2 Functional Requirements

## Purpose

This document defines the functional behavior required for Docetra v2. It describes what the system must do from an engineering implementation perspective, while keeping the same product behavior as v1.

## Functional scope

Docetra v2 must support:
- Unified record management.
- Document workflows.
- Meeting and meeting-topic tracking.
- Organization and officer management.
- User, role, and permission management.
- Controlled internal and external access.
- File upload and storage integration.
- Search and retrieval.
- Configuration management.
- Administrative logging.
- Reporting support.

## Requirement structure

Each functional area below should be implemented as a clear capability with service boundaries, API endpoints, validation, permissions, and data persistence.

## Record management

### FR-REC-001 Unified record creation
The system must allow the creation of records using a unified record model.

### FR-REC-002 Record type assignment
Every record must be assigned a valid record type.

### FR-REC-003 Record status
Each record must support status tracking.

### FR-REC-004 Record stage tracking
Each record type that uses workflow stages must support stage tracking.

### FR-REC-005 Record history
The system must preserve historical changes for records and support timeline-style history views.

### FR-REC-006 Record ownership context
Each record must be associated with an owning or related organizational context.

### FR-REC-007 Record details
The system must allow dynamic record attributes to be stored and retrieved per record type.

### FR-REC-008 Record relations
The system must support links between records where business rules require it.

### FR-REC-009 Record search
The system must support search across record type, title, status, stage, organization, and other relevant indexed fields.

## Document management

### FR-DOC-001 Document records
The system must support document records as a first-class record type.

### FR-DOC-002 Document workflows
The system must support workflow visibility for documents, including current stage and waiting state.

### FR-DOC-003 Incoming and outgoing handling
Where required by the business model, incoming and outgoing documents must be distinguishable in the workflow.

### FR-DOC-004 Document history
Document changes must be visible in history and timeline views.

## Meeting management

### FR-MTG-001 Meeting records
The system must support meeting records.

### FR-MTG-002 Meeting topic records
The system must support meeting-topic records linked to meetings.

### FR-MTG-003 Meeting workflow
The system must support active and unfinished meeting tracking.

### FR-MTG-004 Meeting history
The system must preserve meeting history and allow timeline-based review.

### FR-MTG-005 Meeting-topic linking
The system must support dragging a meeting into a meeting-topic container. Once linked, the meeting must be removed from the standalone meeting board or list and shown only inside the topic container.

### FR-MTG-006 Meeting-topic child display
The system must display child meetings inside a meeting-topic container in a vertical list following the configured ordering rule.

## Organization management

### FR-ORG-001 Organization records
The system must support organizations, including departments, companies, and government structures.

### FR-ORG-002 Organization hierarchy
The system must support parent-child relationships between organizations where needed.

### FR-ORG-003 Organization metadata
The system must allow organization metadata such as sector, purpose, contact details, and identifiers.

### FR-ORG-004 Organization history
The system must preserve organization changes over time.

## Officer and user management

### FR-PEO-001 Officer records
The system must support officer records as the main business-side person entity.

### FR-PEO-002 User account mapping
The system must support a user account linked to an officer.

### FR-PEO-003 Unlinked officers
The system must allow officers to exist without user accounts.

### FR-PEO-004 Role assignment
The system must support role assignment for access control.

### FR-PEO-005 Permission assignment
The system must support permissions assigned to roles or similar access entities.

## Access and sharing

### FR-ACC-001 Internal access
Internal users must be able to access records according to role and organizational scope.

### FR-ACC-002 External access
External company users must only access records and shared resources relevant to their permitted company context.

### FR-ACC-003 Controlled sharing
The system must support controlled sharing of records with related companies or organizational groups.

### FR-ACC-004 Server-side enforcement
All access rules must be enforced on the backend.

## Storage and file handling

### FR-STR-001 File upload
The system must allow users to upload files.

### FR-STR-002 File metadata
Uploaded files must create persistent file metadata records.

### FR-STR-003 Object storage integration
The system must store file objects in the configured object storage.

### FR-STR-004 File-to-record linking
Files must be linkable to records.

### FR-STR-005 Storage synchronization
The system must support Google Drive synchronization if enabled in the configuration.

## Search and retrieval

### FR-SRH-001 Global search
The system must support global search across records and related resources.

### FR-SRH-002 Filtered search
The system must support filtering by type, organization, status, and stage where applicable.

### FR-SRH-003 Search relevance
Search results should prioritize useful operational fields such as title, type, and status.

## Configuration management

### FR-CFG-001 Record type management
The system must support managing record types.

### FR-CFG-002 Record attribute management
The system must support managing record attributes by record type.

### FR-CFG-003 Document type management
The system must support managing document types.

### FR-CFG-004 Application settings
The system must support application configuration and settings.

### FR-CFG-005 Visibility and access for settings
Settings must support visibility and access flags where needed.

## Administrative logging

### FR-LOG-001 Audit logging
The system must record significant actions in an audit log.

### FR-LOG-002 Audit metadata
Audit logs must capture action type, target entity, row reference, timestamp, actor, and request context where available.

### FR-LOG-003 Notification log handling
The system should support log-based notification processing where required by the architecture.

## Reporting support

### FR-RPT-001 Reporting data
The system must make operational data available in a form suitable for reporting.

### FR-RPT-002 Export support
The system must support export-oriented data shaping.

### FR-RPT-003 Future BI readiness
The system should keep reporting structures compatible with future BI expansion.

## Non-functional implementation expectations

The implementation of functional requirements must also respect:
- auditability.
- traceability.
- performance.
- maintainability.
- permission safety.
- storage reliability.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `02-domain-model.md`
- `04-permissions-and-access.md`
- `05-user-flows.md`
- `06-api-contracts.md`
- `07-data-model.md`
- `modules/*`
