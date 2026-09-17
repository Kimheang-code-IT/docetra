# Docetra Project Brief

## Project overview
Docetra is a centralized administrative management platform designed to coordinate cross-department administrative processes, with a primary focus on documents, meetings, and activity logs.

The platform is intended to centralize administrative operations, improve management and monitoring processes, reduce missed or forgotten documents and meetings, and provide structured data for reporting and business intelligence.

## Primary users
- Officers and staff in all departments.
- External company users with access to records related to their company and shared resources.

## Stakeholders and ownership
- Main stakeholders: Operations team.
- System owner: IT team.

## Problem statement
Current administrative data and workflows are scattered across chats, spreadsheets, paper, and disconnected tools. This makes it difficult to track document status, link meetings to topics, produce reliable reports efficiently, and avoid missed follow-ups or forgotten operational tasks.

## Product goals
- Centralize administrative operations in one platform.
- Improve process visibility, operational monitoring, and follow-up tracking.
- Reduce the risk of missed, delayed, or forgotten documents and meetings.
- Enable structured reporting and future business intelligence use cases.
- Provide a history-first operational view, including inline timeline history for records and organizations.

## Core product concept
Docetra is built around a unified record-based model. Multiple business items are stored through a shared `record` structure and differentiated by `record_type`.

Initial record types include:
- document
- meeting
- meeting-topic
- approved-master-list
- master-list-request
- extension-of-validity
- physical-inspection
- tax-incentive
- file
- url

This approach supports a consistent operational model while allowing different record types to render dynamic attributes and workflows based on configuration.

## Functional scope
### Core modules
- **Dashboard** for operational overview and KPI summary, with operational tracking as the primary priority.
- **Meeting management** for active and unfinished meetings and meeting topics, with Kanban view for active items and timeline view for history.
- **Document management** for multiple document types, including separate handling of incoming and outgoing documents in Kanban workflows.
- **Master List Request management** as a special workflow presented in Kanban view.
- **Log management** as record lists separated by type and displayed in data-table form.
- **Dynamic Record Detail pages** that render fields and attributes based on record type.
- **Global search** across relevant records and shared resources.

### Supporting modules
- **Organization management** for government structures and companies, using a shared organizational model where appropriate.
- **Officer management**.
- **Role and permission management**.
- **User management**, where login accounts are linked to officers and may not exist for every officer.
- **File upload portal** that uploads files to object storage and creates file records.
- **Google Drive sync** to organize uploaded files and create records from managed folders.
- **Log upload** for batch import of records.

### Administrative modules
- System log.
- Record type management.
- Record attribute management by record type.
- Document type management.
- Application information.
- Application configuration.
- Storage management.

## Initial release scope
The initial release focuses on operational tracking and process visibility rather than approval automation.

Included in the initial release:
- Stage-based document tracking.
- Kanban-based workflow management operated by administrative officers.
- Visibility into where a document is, what stage it is in, what it is waiting for, and whether it has been released.
- Meeting and meeting-topic management.
- Administrative log management.
- Unified management of multiple record types through the shared record model.
- Internal and external user access from the start.

## Out of scope for initial release
- Approval workflow automation.
- Advanced automation rules.
- BI dashboards and analytics views.
- Mobile application support.
- External system integrations.

Even though these items are out of scope for the initial release, the system architecture and data model should be designed to support them in future updates without major restructuring.

## Technical direction
- **Backend:** FastAPI.
- **Frontend:** To be selected by the frontend team.
- **Database:** PostgreSQL.
- **Cache:** Redis.
- **Storage:** Cloudflare object storage and Google Drive integration.
- **Architecture style:** Modular monolith.

The recommended modular structure includes:
- **record** module for documents, meetings, meeting topics, logs, and other record-based entities.
- **organization** module for departments, government structures, companies, and related classification data.
- **people_access** module for officers, users, roles, and permissions.
- **storage_integration** module for file upload, object storage, and Google Drive synchronization.
- **admin_config** module for record types, record attributes, document types, app configuration, and system settings.
- **reporting_support** module for exports and reporting-ready data preparation.

A modular monolith is recommended for the initial phase because it offers lower operational overhead, simpler deployment, easier debugging, and better use of limited infrastructure resources while preserving a clean path for future extraction if required.

## Non-functional priorities
- Fast and simple user experience.
- Strong auditability and traceability.
- Powerful search and retrieval.
- Scalability for future growth.
- Easy configuration and extensibility.
- Secure access control.
- Reliable file storage and synchronization.

## Configuration direction
Some currently static reference data may later move into configurable enum-style structures driven by record attributes. Candidate examples include:
- company purpose
- company sector
- document type
- room

This direction should be evaluated carefully to balance flexibility with data integrity and administration complexity.

## Success criteria
- Staff can track active documents and operational items clearly through Kanban-based workflow views.
- Meetings, meeting topics, and related records are visible, searchable, and manageable in a structured way.
- The system reduces missed follow-up items and forgotten operational tasks.
- Historical activity is preserved and viewable through timeline-style history.
- Organization-related changes and history are also tracked and shown inline as timeline-based records.

## Expected outcomes
After launch, the expected outcomes are:
- Staff can work faster with less manual follow-up.
- Management can monitor operations in one place.
- Departments and companies can follow related records more clearly.
- Reporting becomes easier, more structured, and more reliable.

## Notes for next documents
This project brief should be followed by:
1. Business Requirements Document.
2. Functional Requirements Document.
3. User Flow and Screen Mapping.
4. Technical Design Document.
5. Permission Matrix and Access Rules.
6. Data Model and Record Attribute Specification.
