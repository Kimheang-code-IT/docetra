# docetra-reporting-support

## Purpose

Use when implementing or modifying operational summaries, dashboards, exports, cross-module read models, or BI-facing data preparation.

## Source Documents

- docs/specification/modules/reporting-support.md

## Domain Overview

The reporting support module prepares operational data for exports, summaries, dashboards, and future BI use. It does NOT own source-of-truth business data — it shapes data from other modules into read-optimized reporting views. It must not implement business workflows or permission ownership.

## Key Entities

| Entity | Responsibility |
|---|---|
| Reporting dataset | Read-optimized structure derived from core operational tables |
| Export-ready view | Shaped result used for spreadsheet exports or downloadable reports |
| Read model | Derived representation optimized for query performance and reporting use |

## Relationships

- Reads from: record (record data), organization (org-based summaries), people_access (access-aware reporting), admin_config (type/setting lookup).
- Owns only derived structures: reporting views, materialized views, export staging tables, read models (clearly derived and maintained by the reporting layer).

## Business Rules

- Reporting MUST respect access control.
- Reporting data MUST be derived from authoritative tables.
- Summaries MUST be consistent across environments.
- Sensitive fields MUST be excluded when unauthorized.
- Exports MUST NOT expose unauthorized data.
- The module MUST NOT own source-of-truth transactional tables.
- The module MUST NOT implement business workflows or permission ownership.
- Reporting logic MUST be isolated from transaction logic.
- Keep the system compatible with future BI expansion without forcing BI into the core product.

## Permissions

- All reporting/exports are access-aware: authorization comes from people_access context. Exact rules: `Needs verification` (04-permissions-and-access.md was not provided).

## API Rules

The module MAY expose APIs for:

- Operational summaries.
- Export generation.
- Filtered report retrieval.
- Dataset refresh or status endpoints (if needed).

Exact routes/payloads: `Needs verification`.

## Data Rules

- May own: reporting views, materialized views, export staging tables, read models.
- MUST NOT own: source-of-truth transactional tables (records, organizations, users, etc.).
- Derived datasets MUST be refreshed correctly.

## Validation Rules

- Reporting filters MUST be valid.
- Access-aware reporting rules MUST be respected.
- Derived datasets MUST be refreshed correctly.
- Exports MUST NOT expose unauthorized data.

## Edge Cases

- User requests an export containing data outside their permission scope → unauthorized fields/rows MUST be excluded. (Derived from specification: "exports do not expose unauthorized data".)
- Stale read model vs authoritative table → refresh must bring the derived dataset back in line. (Derived from specification: "derived datasets are refreshed correctly".)

## Implementation Guidance

- Optimize for read performance WITHOUT changing business ownership.
- Prefer derived data over duplicated manual syncs.
- Make export formats predictable and versionable.
- Keep reporting isolated from transaction logic (no writes to source tables).

## DO NOT

- DO NOT write to or own source-of-truth business tables.
- DO NOT bypass access control in summaries or exports.
- DO NOT duplicate business workflow logic here.
- DO NOT own permissions.

## Testing Checklist

- [ ] Summary data reflects authoritative tables.
- [ ] Invalid reporting filters are rejected.
- [ ] Unauthorized user cannot see restricted data in summaries.
- [ ] Export excludes unauthorized fields/rows.
- [ ] Derived datasets refresh correctly.
- [ ] Reporting layer performs no writes to business tables.
- [ ] Same query yields consistent summaries across environments.

## Needs Verification

- Exact API contracts (06-api-contracts.md not provided).
- Refresh mechanism (materialized views vs on-demand).
- Export formats supported.
