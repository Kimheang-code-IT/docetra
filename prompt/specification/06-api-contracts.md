# Docetra v2 API Contracts

## Purpose and authority

This document defines the stable REST contract for Docetra v2. Module documents define resource-specific fields; `prompt/backend/00-integration-contract.md` defines the detailed implemented frontend boundary. If wording conflicts, reconcile the documents before implementation rather than silently diverging.

## Base and transport

- Base path: `/api/v2`.
- JSON for normal requests and responses; multipart only for file transfer.
- TLS is mandatory outside local development.
- Resource names are plural and stable. Breaking changes require a new API version or a backward-compatible migration.
- Request IDs flow through proxy, API, jobs, logs, and error responses.

## Authentication and authorization

Browser authentication uses a server-side session in a `Secure`, `HttpOnly`, `SameSite` cookie.

| Method | Path | Contract |
| --- | --- | --- |
| POST | `/auth/login` | Validate credentials, set session/CSRF cookies, return safe user |
| GET | `/auth/me` | Validate session; return current user and flattened `pageAccess` capabilities |
| POST | `/auth/logout` | Revoke session and clear cookies |

The frontend includes credentials and sends `X-CSRF-Token` from the readable `XSRF-TOKEN` cookie on protected mutations. CORS uses an explicit origin allow-list and never wildcard origins with credentials. Session secrets are never returned in JSON, URLs, browser local storage, or logs.

Every protected API performs server-side capability, tenant, ownership, resource, and field checks. Frontend middleware and hidden actions are not security boundaries. `ALL_PAGES` is valid only for a trusted super-admin policy.

## Methods and mutation safety

- `GET`: read only.
- `POST`: create or a documented non-idempotent action.
- `PATCH`: partial update with optimistic version/ETag.
- `DELETE`: normal UI delete, implemented as an auditable soft delete unless an endpoint explicitly says purge.

Lifecycle permissions are separate: `.archive`, `.restore`, `.delete`, and `.purge`. Creator-scoped users may restore their own archived records but never purge. A soft-deleted record is recoverable only by an administrator. Permanent purge uses `DELETE /{resource}/{id}/purge`, is never creator-scoped, and enforces dependency, retention, legal-hold, and last-administrator protections.

Use idempotency keys for retryable creates, uploads, exports, and other operations that could be duplicated. Return `409` for stale versions or uniqueness conflicts.

## Response envelopes

Detail: `{ "data": { ... } }`.

List: `{ "data": [ ... ], "meta": { "page": 1, "limit": 20, "total": 100, "totalPages": 5 } }`.

Error: `{ "error": { "code": "machine_code", "message": "Safe message", "fields": {}, "requestId": "req_..." } }`.

Status meanings:

- `400` malformed request.
- `401` missing or expired session; the client opens the session dialog.
- `403` authenticated but forbidden; the client opens the permission dialog and does not navigate to a special page.
- `404` missing or deliberately concealed resource.
- `409` uniqueness, state, or optimistic-version conflict.
- `422` typed field validation.
- `429` rate limited.
- `5xx` server failure without internal implementation details.

## Pagination, filtering, and search

All list and option endpoints are bounded. They consistently accept `page`, `limit`, `q`, `sort`, and documented filters; cursor pagination may replace page pagination for logs. Apply permission and tenant filters before counts and pagination. Search and AI-assisted search must never reveal redacted resources or fields.

## Lifecycle and workflow

Business records, meetings/topics, and configuration/master-data cards expose only `active`, `archived`, and `deleted`. “Completed” is not a lifecycle status. Workflow uses a separate `stageId`; terminal behavior belongs to stage metadata such as `isFinal`. User-account and asynchronous-job state machines remain separate domain-specific enums.

## Assignment references

Assignee values are arrays of `{ id, label, type }`, where type is `officer`, `department`, or `company`. The server resolves labels, de-duplicates references, preserves order, validates scope, and permission-filters option search. Option endpoints accept indexed `q`, optional `type`, and bounded `limit` parameters.

## Resource families

- Meetings: topics, history, reorder, assignment, attachments, links, card soft delete.
- Records: incoming, outgoing, documents, master list, dynamic details, history, links, logs, attachments.
- Organization: departments, companies, purposes, sectors, officers, hierarchy.
- People/access: users, roles, permission catalog, identity resolution.
- Configuration/settings: record types, attributes, app information, localization, storage, integrations.
- Portal/operations: uploads, Drive sync, jobs, portal/system audit logs.
- Shared: comments, activity, attachments, exports, and permission-aware search.

## Localization and time

App configuration supplies language, locale, IANA timezone, date/time formats, first day of week, number format, currency, page size, and card-field defaults. Store timestamps in UTC and serialize ISO 8601. Never hard-code display locale or timezone in a page or endpoint.

## Uploads, audit, and asynchronous work

The server enforces upload count, size, extension, detected MIME, malware scanning, tenant ownership, and storage policy. Long exports, scans, syncs, notifications, and indexing work publish durable RabbitMQ jobs and return `202` with a job ID and bounded polling contract. Consumers are idempotent because delivery is at least once; retry is bounded and exhausted work moves to a dead-letter queue. Permission, configuration, upload, archive, restore, soft delete, purge, workflow, comment, attachment, and sensitive-setting changes produce immutable activity/audit events.

APScheduler is the authoritative timer engine for meetings. Meeting writes upsert or remove persistent schedules after commit; due callbacks publish RabbitMQ events. Meeting responses expose timezone, reminder offsets, next scheduled action, and operational schedule state. Browser timers are presentation-only and must never be authoritative.

Telegram Meeting Bot, Telegram Development Bot, and email are separate provider adapters and RabbitMQ routes. Forgot-password always returns a uniform accepted response, stores only a short-lived single-use token hash, sends through the configured third-party email provider, and revokes active sessions after reset. Bot/provider secrets are never returned by APIs.

Optional Google Sign-In, Calendar, Drive, and Gmail capabilities are independently enabled backend adapters. OAuth authorization-code/PKCE state is server-bound; tokens are encrypted backend-only. Calendar and Drive commands are asynchronous, idempotent, permission-checked projections through RabbitMQ, while Docetra remains the authoritative business record. Safe status/connect/revoke/sync APIs follow `prompt/backend/05-google-workspace-integration.md`.

Safe GETs may use tenant/permission-scoped Redis cache-aside reads. Frequently changing resources use the short tier; stable configuration/reference data uses the long tier. Mutations invalidate impacted cache keys after commit, with transactional-outbox events repairing other instances. Authentication/authorization truth and sensitive response bodies are never served from an unsafe shared cache.

## Contract verification

- Publish OpenAPI schemas for all non-mock endpoints.
- Test success/error envelopes, session/CSRF behavior, capability boundaries, field redaction, lifecycle values, option scoping, and version conflicts.
- Test cache isolation/invalidation/fallback and duplicate/retried/dead-lettered job delivery.
- Keep frontend adapter contract tests and backend schema tests in CI.
- Disable mock data in deployed environments.

## Related documents

- [`01-system-architecture.md`](./01-system-architecture.md)
- [`04-permissions-and-access.md`](./04-permissions-and-access.md)
- [`05-user-flows.md`](./05-user-flows.md)
- [`07-data-model.md`](./07-data-model.md)
- [`../backend/00-integration-contract.md`](../backend/00-integration-contract.md)
