# Docetra v2 Migration Notes

## Purpose

This document captures brief migration notes for the move from Docetra v1 to Docetra v2. It is intentionally short and implementation-focused so that the main v2 specs remain clean and product-centered.

## Migration principle

Docetra v2 should be treated as a clean rewrite with v1 as the behavior reference.

The migration notes should only explain items that matter during implementation, data continuity, or rollout.

## What must carry over

The following v1 concepts should remain recognizable in v2:
- unified record model.
- record types and type-driven behavior.
- organization context.
- officer and user mapping.
- role and permission behavior.
- record history and timeline visibility.
- file upload and storage linkage.
- external company access.
- configuration-driven behavior.

## What should improve

The v2 rewrite should improve:
- code structure.
- module boundaries.
- naming consistency.
- data model clarity.
- API versioning.
- testability.
- maintainability.
- deployment repeatability.

## Legacy considerations

Any v1-specific quirks should not be copied into the main v2 specification unless they affect implementation.

If a legacy behavior must be preserved for compatibility, document it here only as a migration note.

## Data migration guidance

- Preserve important operational history where possible.
- Map old concepts to the new unified record model carefully.
- Review record type and attribute mappings before migration.
- Validate organization and officer identity mappings.
- Confirm permission mappings before enabling access in v2.
- Reconcile file references and storage paths before cutover.

## Cutover considerations

The team should plan for:
- data validation before release.
- permission validation before external access.
- history verification after import.
- file integrity verification.
- staged rollout if needed.

## Exclusions

This document does not define:
- the full migration architecture.
- detailed ETL steps.
- rollback engineering.
- operational runbooks.

Those topics should be added only if the migration plan requires them.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `02-domain-model.md`
- `03-functional-requirements.md`
- `04-permissions-and-access.md`
- `07-data-model.md`
- `09-implementation-plan.md`
