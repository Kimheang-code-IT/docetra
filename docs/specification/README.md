# Docetra v2 Documentation

This folder contains the engineering specification for Docetra v2.

Docetra v2 is a clean rewrite of Docetra v1 with the same business goals and user-facing behavior, but with improved structure, clearer boundaries, and cleaner implementation contracts.

## Documentation structure

### Core system docs
- `00-overview.md` — product intent, scope, assumptions, and document map.
- `01-system-architecture.md` — modular monolith structure, tech baseline, and architecture rules.
- `02-domain-model.md` — business domains and core concepts.
- `03-functional-requirements.md` — capability-level requirements.
- `04-permissions-and-access.md` — role, department, and external access rules.
- `05-user-flows.md` — primary user journeys and workflow transitions.
- `06-api-contracts.md` — REST API conventions and endpoint expectations.
- `07-data-model.md` — database entities, relationships, and integrity expectations.
- `08-shared-standards.md` — naming, validation, audit, storage, and testing standards.
- `09-implementation-plan.md` — build order and delivery phases.
- `10-migration-notes.md` — brief v1-to-v2 carryover notes.

### Module docs
- `modules/record.md` — unified record behavior, workflow, history, and relationships.
- `modules/organization.md` — organizations, hierarchy, and classification.
- `modules/people-access.md` — officers, users, roles, permissions, and access checks.
- `modules/storage-integration.md` — file upload, object storage, and Google Drive sync.
- `modules/admin-config.md` — record types, attributes, settings, and configuration.
- `modules/reporting-support.md` — read models, summaries, and export support.

## Reading order

Recommended reading order for implementation:
1. `00-overview.md`
2. `01-system-architecture.md`
3. `02-domain-model.md`
4. `04-permissions-and-access.md`
5. `07-data-model.md`
6. Module docs
7. `03-functional-requirements.md`
8. `05-user-flows.md`
9. `06-api-contracts.md`
10. `08-shared-standards.md`
11. `09-implementation-plan.md`
12. `10-migration-notes.md`

## Notes

- v2 should be treated as a replacement for v1.
- The docs assume an engineering-only audience.
- The baseline stack is FastAPI, PostgreSQL, Redis, and Docker-based deployment on DigitalOcean.
- API versioning should start at `/api/v2`.
- Migration-specific details should stay brief and isolated in `10-migration-notes.md`.
