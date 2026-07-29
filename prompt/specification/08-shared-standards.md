# Docetra v2 Shared Standards

## Purpose

This document defines the shared implementation standards used across Docetra v2. It exists to keep the engineering team aligned on naming, structure, validation, error handling, audit behavior, and code organization.

## Code organization standards

- Keep business logic inside the correct module.
- Avoid mixing domain logic with transport or UI logic.
- Keep shared utilities small and intentionally scoped.
- Prefer explicit service boundaries over hidden helper dependencies.
- Use module-level ownership for tables, services, and APIs.

## Naming standards

- Use clear, consistent English names for tables, fields, services, and endpoints.
- Prefer domain-driven names over generic technical names.
- Keep record type codes stable.
- Use the same naming pattern across backend, database, and API documents where possible.

## API standards

- Use REST-first resource naming.
- Keep API versions explicit.
- Return consistent payload structures.
- Use predictable error categories.
- Keep permission enforcement on the backend.
- Avoid exposing database internals in API responses.

## Validation standards

- Validate input at the API boundary.
- Revalidate important business rules in the service layer.
- Do not trust the client for access decisions.
- Keep record-type-specific validation close to the module that owns the record type.
- Return clear and actionable validation messages.

## Audit standards

- Record significant actions in audit logs.
- Include actor, action, target entity, and timestamp where relevant.
- Capture access-control or configuration changes when they matter.
- Preserve history instead of overwriting important operational facts.

## History standards

- History must be append-oriented wherever possible.
- Changes that matter operationally should be visible in timeline views.
- Do not lose past state when updating records.
- Keep history data queryable for support and reporting.

## Access standards

- All protected endpoints must enforce authorization.
- Internal and external access rules must be enforced consistently.
- Permission checks should be centralized.
- Avoid duplicating access logic across handlers.
- Treat sharing as explicit, not implicit.

## Storage standards

- Store binary files in the configured object storage.
- Store file metadata in PostgreSQL.
- Keep storage-specific details separate from business record logic.
- Track sync state if external storage integrations are enabled.

## Error handling standards

- Use clear, stable error codes where practical.
- Distinguish validation, authentication, authorization, conflict, and server errors.
- Do not leak stack traces or internal implementation details to clients.
- Keep client-facing error messages concise and actionable.

## Testing standards

- Add unit tests for domain logic.
- Add integration tests for database and module behavior.
- Add API contract tests for stable endpoints.
- Test permission rules explicitly.
- Test history preservation and audit generation for important flows.

## Deployment standards

- Use Dockerized deployment.
- Keep environment-specific configuration externalized.
- Separate dev, staging, UAT, and production settings.
- Make deployment repeatable and predictable.

## Documentation standards

- Keep each document focused on one concern.
- Use the overview as the source of structural intent.
- Keep module docs implementation-ready.
- Record migration notes separately when needed.
- Avoid mixing v1 quirks into the main v2 specification.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `02-domain-model.md`
- `03-functional-requirements.md`
- `04-permissions-and-access.md`
- `05-user-flows.md`
- `06-api-contracts.md`
- `07-data-model.md`
- `modules/*`
