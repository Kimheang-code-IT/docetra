# Docetra v2 Overview

## Purpose

Docetra v2 is a replacement for the existing Docetra v1 system. It keeps the same business goals and user-facing behavior as v1, but the internal structure, naming, boundaries, and documentation are rewritten cleanly for maintainability, implementation clarity, and future extensibility.

This document defines the product intent, scope boundaries, assumptions, and the documentation structure for the engineering team.

## Product summary

Docetra is a centralized administrative record management platform for cross-department coordination, operational tracking, and controlled external access. The system is built around a unified record model that can represent documents, meetings, meeting topics, logs, files, URLs, and other record-based business items.

The primary purpose of the platform is to provide one operational source of truth for administrative records, their current status, and their history.

## Relationship to v1

Docetra v2 is a replacement for v1 with the same business goals and the same core behavior. The rewrite is intended to clean up internal structure, reduce coupling, improve modularity, and make the system easier to maintain and extend.

This document does not treat v1 as the source of truth for implementation details. Instead, v1 is treated as the existing behavior baseline, while v2 defines the target implementation shape.

## Audience

This documentation is written for engineering teams only.

It is intended to support:
- Backend development.
- Frontend development.
- Database design.
- API implementation.
- System integration.
- QA and test planning.
- Deployment and operational setup.

## Core goals

Docetra v2 must:
- Centralize administrative operations in one platform.
- Track records by type through a unified model.
- Preserve history and timeline visibility.
- Support cross-department coordination.
- Support controlled internal and external access.
- Provide reliable search and retrieval.
- Remain extensible for future automation and reporting.

## Scope

### In scope
- Record tracking by type.
- Status and stage visibility.
- Record history and timeline visibility.
- Meeting and meeting-topic tracking.
- Document workflows.
- Organization and officer management.
- Role and permission management.
- Controlled sharing with external companies.
- File upload and storage integration.
- Search across relevant records.
- Configuration and metadata management.

### Out of scope
- Advanced approval automation.
- Advanced automation rules.
- Advanced BI dashboards.
- Mobile application support.
- Full external system integrations.
- Major product scope expansion beyond v1 parity plus cleanup.

## Product principles

Docetra v2 should follow these principles:
- Keep the operational model simple and explicit.
- Preserve historical traceability for all important changes.
- Prefer clear module boundaries over shared hidden logic.
- Design for future expansion without overengineering the first release.
- Keep the API and data model consistent and predictable.
- Favor configuration where behavior differs by record type.

## Technical baseline

The default technical baseline from v1 is:
- Backend: FastAPI.
- Frontend: selected by the frontend team.
- Database: PostgreSQL.
- Cache: Redis.
- Messaging: RabbitMQ with independently scalable background workers.
- Scheduling: APScheduler for persistent meeting timers and recurrence orchestration.
- Storage: Cloudflare object storage plus Google Drive integration.
- Architecture style: modular monolith.

The rewrite should keep this baseline unless a later specification explicitly changes it.

## Architecture direction

The system should be organized as a modular monolith with clear internal module boundaries. Recommended modules include:
- record.
- organization.
- people_access.
- storage_integration.
- admin_config.
- reporting_support.

The purpose of the modular structure is to reduce coupling, keep responsibilities clear, and make future extraction possible if needed.

## API direction

Docetra v2 should use REST-first APIs. Internal event-driven or RPC-style patterns may be introduced later if needed, but they should not be required for the core design of v2.

API versioning should be explicit from the start, such as `/api/v2`.

## Deployment direction

The default deployment assumption is Docker-based self-hosted deployment on DigitalOcean.

This supports:
- predictable infrastructure.
- lower operating cost.
- straightforward deployment automation.
- a practical fit for a modular monolith.

## Environments

The standard environment strategy is:
- Development.
- Staging.
- UAT.
- Production.

Each environment should be treated as a separate deployment target with its own configuration and data handling rules.

## Testing baseline

The minimum testing scope for v2 is:
- Unit testing.
- Integration testing.
- API contract testing.

Additional end-to-end and regression testing may be added later, but they are not required to define the core v2 documentation package.

## Assumptions

- v1 behavior is the baseline reference for expected product behavior.
- v2 may improve internal design, naming, and structure without changing the core user-facing contract.
- Officers and login accounts may remain linked but not strictly one-to-one.
- Manual operational workflows remain part of the product baseline.
- Future automation support should not be blocked by the v2 design.

## Constraints

- The system must remain maintainable by a small engineering team.
- The rewrite should not introduce unnecessary architectural complexity.
- Internal module boundaries should be explicit.
- History and auditability must be preserved.
- External access must remain controlled and permission-driven.
- The system should remain practical to deploy and operate in a Docker-based environment.

## Non-goals

- Rewriting the business domain into a different product shape.
- Introducing major new workflow automation in the core rewrite.
- Moving to a microservices architecture for v2.
- Introducing mobile-first behavior.
- Optimizing for advanced BI before operational tracking is stable.

## Documentation package

This overview is the entry point for the rest of the v2 documentation set.

Recommended companion documents:
- `01-system-architecture.md`
- `02-domain-model.md`
- `03-functional-requirements.md`
- `04-permissions-and-access.md`
- `05-user-flows.md`
- `06-api-contracts.md`
- `07-data-model.md`
- `08-shared-standards.md`

Recommended module documents:
- `modules/record.md`
- `modules/organization.md`
- `modules/people-access.md`
- `modules/storage-integration.md`
- `modules/admin-config.md`
- `modules/reporting-support.md`

## Migration notes

v1 should be treated as the behavioral reference point only. Migration-specific details should be documented separately and kept brief so that the main v2 specification stays focused on the target system.
