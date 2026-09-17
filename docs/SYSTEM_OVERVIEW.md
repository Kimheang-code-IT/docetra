# Docetra — System Overview

**Docetra** is a Document & Meeting Management System: a modular-monolith backend (FastAPI + PostgreSQL) with a Nuxt 3 frontend, built around a **unified record engine** where every business item (meetings, topics, incoming/outgoing documents, master list requests) is a *record type* with configurable fields, stages, and permissions.

## Stack

| Layer | Technology |
|---|---|
| Frontend | Nuxt 3 (Vue 3, TypeScript, Pinia), i18n (English + Khmer), Vitest + Playwright |
| Backend | FastAPI (Python 3.12), async SQLAlchemy 2, Alembic |
| Database | PostgreSQL (business + authorization truth) |
| Cache/session | Redis (ops DB 0, short cache DB 1) |
| Jobs/queue | RabbitMQ (worker as a separate process; APScheduler runs in-API by default via `SCHEDULER_IN_API`) |
| Object storage | MinIO (S3 API) |
| Edge | Nginx (Compose edge: serves the static SPA + proxies `/api`) |

## Architecture

```
Nuxt SPA ── /api/v2 ──► FastAPI (api + application layer)
                          │
        ┌─────────────────┼──────────────────┐
   modules/*        platform/*          jobs/*
   (record, org,    (audit, messaging)  (worker, scheduler,
   people_access,                        RabbitMQ consumers)
   organization,
   storage_integration,
   admin_config,
   reporting_support)
        │
   repositories → SQLAlchemy → PostgreSQL        MinIO ◄── storage_integration
   Redis ◄── cache/session                       SMTP/Telegram/Google Drive ◄── integrations
```

### Backend module map (`backend/app/`)

| Path | Responsibility |
|---|---|
| `modules/record` | Unified record engine: record types, dynamic attributes, stages, attachments, meetings/topics, logs, collaboration |
| `modules/organization` | Departments, companies, sectors, purposes (hierarchy + lookup) |
| `modules/people_access` | Users, roles, permissions, officers, identity, auth endpoints |
| `modules/storage_integration` | File metadata, uploads, providers, Google Drive sync, portal |
| `modules/admin_config` | Record type/attribute configuration API, settings, storage settings |
| `modules/reporting_support` | Dashboard, global search, mentions, exports |
| `platform/` | `audit` (audit_log, notification_audit_log), `messaging` (outbox) |
| `core/` | auth/JWT, permissions, authorization, cache, errors, rate limit, redaction, config |
| `application/` | Cross-module composition (attachment upload flow, export/organization/people routers) |
| `jobs/` | RabbitMQ topology, consumers (exports, outbox), scheduler (cleanup, meeting reminders, reconcile) |
| `integrations/` | Email (SMTP), Telegram bots, Google Drive client, object store (S3/MinIO) |

### Key numbers (verified)

- **355 registered API operations** under `/api/v2`
- **28 SQLAlchemy tables**, Alembic head `0012_drop_favorites`
- **19 frontend entity adapters** driven by one config file (`frontend/app/config/entities.ts`)
- Backend tests: 49 test files (unit/contract/integration/architecture); frontend: 9 unit files, 79 tests

## Domain model in one paragraph

A **RecordType** defines a family of records (`meeting_topic`, `meeting_history`, `incoming_document`, `outgoing_document`, `document`, `master_list_request`, plus admin-created types). **RecordAttribute** is a reusable field catalog; **RecordTemplate** maps attributes into a type (required/ordering); **RecordStageTemplate** defines workflow stages. A **Record** holds core fields + `record_content`/`record_metadata` JSON; **RecordDetail** stores typed dynamic attribute values; **RecordAttachment** links records to **File** metadata whose bytes live in MinIO; **RecordOrganization** links records to **Organization**s (department/company) with a role. **User**s authenticate, map to **Officer**s, and get **Permission** rows through **Role**s (with `scope = all | creator`). Everything mutating is written to **audit_log**; lifecycle is `active → archived → (deleted → purged)`.

## Frontend pages → backend resources

| Page | Route | Backend resource |
|---|---|---|
| Dashboard | `/` | `GET /dashboard/summary` |
| Meeting Topic | `/meetings/topics` | `records/meeting_topic` |
| Meeting History | `/meetings/history` | `records/meeting_history` |
| Incoming Document | `/records/incoming-documents` | `records/incoming_document` |
| Outgoing Document | `/records/outgoing-documents` | `records/outgoing_document` |
| Document (combined) | `/records/documents` | `records/document` |
| Master List Request | `/records/master-list-requests` | `records/master_list_request` |
| Record Logs | `/records/logs` | `records/logs` |
| Department / Company | `/organizations/{type}` | `organizations/{org_type}` |
| Purpose / Sector | `/purpose`, `/sector` | `purpose`, `sector` |
| Officer | `/officers` | `officers` |
| File Upload / Drive Sync / Portal Logs | `/portal/...` | `portal/*` |
| Roles / Users | `/user-management/...` | `users/roles`, `users` |
| Record Type / Attribute Catalog | `/configuration/...` | `configuration/record-types`, `configuration/record-attributes` |
| App Info / App Config / Storage | `/settings/...` | `settings/*` |
| Archive | `/archive` | per-source `archive`/`restore` endpoints |
| System Logs | `/system-monitor/system-logs` | `system/logs` |

Detailed docs: see [FRONTEND.md](FRONTEND.md), [BACKEND.md](BACKEND.md), [DATABASE.md](DATABASE.md), [API.md](API.md), and the flow documents.
