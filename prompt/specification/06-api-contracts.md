# Docetra v2 API Contracts

## Purpose

This document defines the API design conventions and contract expectations for Docetra v2. It is intended to keep backend and frontend implementation aligned while maintaining a clean REST-first architecture.

## API principles

- REST-first.
- Versioned from the start.
- Predictable request and response shapes.
- Consistent error handling.
- Server-side authorization on every protected route.
- Minimal coupling to database structure.
- Clear resource naming.

## Base API pattern

All public API endpoints should be exposed under a versioned base path such as:

- `/api/v2`

The exact routing structure may vary by deployment, but versioning must remain explicit.

## Resource conventions

Resources should be named using clear plural forms where appropriate.

Examples:
- `/records`
- `/record-types`
- `/organizations`
- `/officers`
- `/users`
- `/roles`
- `/permissions`
- `/files`
- `/settings`
- `/audit-logs`

## Standard HTTP methods

Use standard REST semantics where possible:
- `GET` for reading.
- `POST` for creating.
- `PUT` or `PATCH` for updating.
- `DELETE` for deleting or archiving when allowed.

## Response shape

Responses should be consistent across modules.

A recommended structure is:
- `data` for the main payload.
- `meta` for pagination or context.
- `errors` for validation or business errors.

The implementation team may refine the exact schema, but it should remain stable across the API.

## Error handling

API errors should be:
- clear.
- machine-readable.
- safe for clients.
- free from internal stack details.

Recommended categories:
- validation error.
- authentication error.
- authorization error.
- not found.
- conflict.
- server error.

## Pagination and filtering

List endpoints should support:
- pagination.
- search terms where relevant.
- sorting where relevant.
- filters by type, stage, status, organization, or access scope.

Pagination behavior should be consistent across list endpoints.

## Record APIs

Record APIs should support:
- list records.
- create record.
- retrieve record detail.
- update record.
- retrieve record history.
- retrieve linked records.
- manage record attachments.
- manage record details or dynamic attributes.

The exact endpoints should be defined per implementation, but the behavior must support the unified record model.

## Organization APIs

Organization APIs should support:
- list organizations.
- create organization.
- retrieve organization detail.
- update organization.
- retrieve organization history.
- manage hierarchy and relationships.

## People and access APIs

People and access APIs should support:
- officer management.
- user account mapping.
- role management.
- permission assignment.
- access lookup.
- identity resolution.

## Storage APIs

Storage APIs should support:
- file upload.
- file metadata retrieval.
- file association with records.
- storage sync operations where enabled.

## Configuration APIs

Configuration APIs should support:
- record type management.
- record attribute management.
- document type management.
- application setting management.
- setting visibility and access rules.

## Audit APIs

Audit APIs should support:
- audit log listing.
- audit log detail retrieval.
- filtering by entity, action, actor, and date range.

## Search APIs

Search APIs should support:
- global search.
- resource-specific search.
- permission-aware result filtering.

## API version stability

The v2 API should be treated as the stable contract for this rewrite. Breaking changes should be handled through explicit versioning or backward-compatible migration steps.

## Implementation notes

- Keep endpoint behavior consistent with role and access rules.
- Prefer resource-oriented endpoints over action-heavy custom routes unless the business case requires otherwise.
- Document request and response schemas for each endpoint in the module-level API docs.
- Use contract tests to protect endpoint behavior.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `03-functional-requirements.md`
- `04-permissions-and-access.md`
- `05-user-flows.md`
- `07-data-model.md`
- `modules/*`
