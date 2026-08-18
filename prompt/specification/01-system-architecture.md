# Docetra v2 System Architecture

## Purpose

This document defines the target system architecture for Docetra v2. It describes how the system is organized, how modules interact, and what architectural rules the engineering team should follow when implementing the platform.

## Architecture summary

Docetra v2 uses a modular monolith architecture. The system is implemented as a single deployable backend application with strong internal module boundaries, a REST-first API layer, and a separate frontend application.

This approach keeps deployment and operations simple while still allowing clean separation of concerns inside the codebase.

## Architectural goals

The architecture must:

- Keep business logic organized by module.
- Reduce hidden coupling between domains.
- Preserve clear boundaries for future extraction if needed.
- Support record history, access control, search, and configuration cleanly.
- Stay practical for a small or medium engineering team.
- Be easy to deploy in a Docker-based environment.



## High-level components



### Backend application

The backend is the central application layer. It exposes REST APIs, applies business rules, manages persistence, coordinates module interactions, and handles security, auditing, and storage integration.

### Frontend application

The frontend is a separate client application that consumes the backend APIs. The exact frontend framework may be chosen by the frontend team, but the backend contract must remain stable and versioned.

### Database

PostgreSQL is the primary database. It stores operational data, configuration data, permissions, records, and audit-related information.

### Cache

Redis provides three logical responsibilities: operational/session coordination, a short TTL cache for frequently changing reads, and a long TTL cache for stable configuration/reference reads. Cache keys are tenant- and permission-scoped, every entry expires, and writes invalidate affected keys after the database transaction commits. Redis must not replace PostgreSQL for durable business state or authorization truth.

### Message broker and workers

RabbitMQ carries durable asynchronous jobs and domain events. Separate worker processes handle file scanning, Drive sync, exports, notifications, search/index projections, recurrence expansion, and cross-instance cache invalidation. Delivery is at least once, so workers must be idempotent and use bounded retry/backoff plus dead-letter queues. A transactional outbox connects PostgreSQL commits to reliable message publication.

### Meeting scheduler

APScheduler is mandatory for meeting reminders, start/end timers, recurrence expansion, cleanup, and schedule reconciliation. It runs as a dedicated process with persistent PostgreSQL schedule storage and UTC as its scheduler timezone. Due callbacks remain short and publish durable RabbitMQ messages; workers perform notifications and business side effects. Do not run a scheduler inside each API process.

### External notification integrations

Provider adapters connect to a transactional email service and two isolated Telegram bots. Meeting Bot sends permission-checked user reminders from APScheduler events. Development Bot sends private deployment/version/code/docs and operational monitoring alerts from signed CI/CD or internal monitoring events. Password-reset email uses single-use hashed tokens, uniform responses, short expiry, and session revocation. External delivery always runs through RabbitMQ workers and cannot block core transactions.

### File storage

Cloudflare object storage is used for uploaded files, while Google Drive integration remains part of the storage-related workflow where required by the product.

Future Google Workspace capabilities are isolated provider adapters: scoped Google Sign-In, Calendar meeting projection, existing Drive synchronization, and optional Gmail delivery. Each capability is independently enabled through backend OAuth 2.0 authorization-code flow with PKCE; credentials and refresh tokens never enter the frontend. Docetra remains authoritative for permissions, lifecycle, workflow, activity, and APScheduler reminders. See `prompt/backend/05-google-workspace-integration.md`.

## Module structure

The backend should be organized into the following major modules:

- `record`
- `organization`
- `people_access`
- `storage_integration`
- `admin_config`
- `reporting_support`

Each module should own its own logic, data access, and internal services as much as possible. Shared utilities should be limited to cross-cutting concerns such as auth, validation, audit logging, and common response patterns.

## Module responsibilities

### record

Handles the unified record model, record types, record history, stages, timelines, attachments, and record-specific business behavior.

### organization

Handles departments, companies, government structures, related organizational metadata, and organization history.

### people_access

Handles officers, user accounts, roles, permissions, and identity mapping.

### storage_integration

Handles file upload, object storage, Google Drive synchronization, file metadata, and storage state.

### admin_config

Handles record types, record attributes, document types, application configuration, and system metadata.

### reporting_support

Handles exports, reporting-ready datasets, and data preparation for operational or future BI ucse.

## Integration boundaries

Modules should communicate through clearly defined interfaces. Direct cross-module table access should be avoided unless explicitly approved in the data model design.

Recommended interaction rules:

- Business logic should stay inside the owning module.
- Shared read models may be created for reporting or search.
- Cross-module writes should go through application services, not ad hoc database logic.
- Audit events should be captured consistently for important changes.



## API layer

The API layer should be REST-first and versioned from the start. The primary public contract should be exposed under `/api/v2`.

The API layer should:

- Validate input.
- Enforce authentication and authorization.
- Call application services.
- Return predictable response shapes.
- Avoid leaking database structure into responses.



## Security model

Security is based on authenticated users, role-based permissions, and department-aware access control. External company users must be isolated to their permitted records and organizations.

The backend must:

- Enforce permission checks server-side.
- Distinguish internal and external user access.
- Preserve auditability for sensitive actions.
- Avoid relying on frontend checks for access control.



## Data persistence strategy

PostgreSQL is the source of truth for business data. The database should store:

- records and record history.
- organizations.
- officers and user mappings.
- roles and permissions.
- configuration and metadata.
- audit log entries.
- storage metadata.

Use Redis only for non-durable operational acceleration and coordination. Use RabbitMQ for delivery, not as the source of job/business state; persist job status, audit, and the transactional outbox in PostgreSQL.

## Audit and history

Auditability is a first-class architectural requirement. Important changes must be recorded in a durable way, and the system should support timeline-style history for records and related organizations.

The architecture should make it easy to capture:

- who changed what.
- when the change happened.
- what entity was affected.
- what the before/after context was, when relevant.



## Storage and file handling

File uploads should be stored in object storage, with metadata persisted in PostgreSQL. The system should be able to link file records to business records and support Google Drive synchronization where needed.

Storage handling should separate:

- file metadata.
- binary object storage.
- business record linkage.
- external sync state.



## Deployment model

Local development deliberately uses a split topology: the Nuxt frontend runs on the developer computer for HMR, while the API, APScheduler process, backend worker, PostgreSQL, Redis, RabbitMQ, and MinIO/S3-compatible storage run in Docker through `compose.backend.yml`. The API explicitly allows only the configured local frontend origin for credentialed requests.

Production remains independently deployable on DigitalOcean: the built frontend may use a managed host or container, and backend services run as containers behind a TLS reverse proxy. PostgreSQL, Redis, RabbitMQ, object storage, workers, and scheduled jobs use private networking and separate credentials. API and worker processes scale independently; frontend hosting is not coupled to the backend Compose topology.

See `prompt/backend/00-integration-contract.md` and `frontend/docs/local-frontend-docker-backend.md` for the operational boundary.



## Environment model

The architecture should support the following environments:

- Development.
- Staging.
- UAT.
- Production.

Each environment should use separate configuration values and independent deployment settings.

## Testing expectations

The architecture should support:

- unit tests for domain and service logic.
- integration tests for database and module interactions.
- API contract tests for stable endpoint behavior.

The codebase should be structured so these tests can be added without major refactoring.

## Extensibility principles

The architecture should remain open for future enhancements such as:

- configurable workflows.
- stronger automation.
- richer reporting.
- more record types.
- future service extraction if required.

The design should avoid premature microservice decomposition while still keeping extraction paths clear.

## Implementation rules

- Keep module boundaries explicit.
- Prefer application services over direct cross-module shortcuts.
- Do not couple business rules to UI logic.
- Keep the database model stable and well-named.
- Preserve history and auditability at the persistence layer.
- Make permission checks mandatory at the backend.



## Related documents

- `00-overview.md`
- `02-domain-model.md`
- `03-functional-requirements.md`
- `04-permissions-and-access.md`
- `06-api-contracts.md`
- `07-data-model.md`
- `08-shared-standards.md`
