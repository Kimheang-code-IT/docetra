# Docetra v2 Module: Reporting Support

## Purpose

The reporting support module prepares operational data for exports, summaries, dashboards, and future BI use. It does not own the source-of-truth business data, but it helps shape that data into useful reporting views.

## Module responsibilities

The reporting support module owns:
- reporting-oriented data shaping.
- export-ready datasets.
- summary views or materialized outputs where needed.
- cross-module read models for reporting.
- data preparation for operational analysis.
- future BI compatibility support.

## Core concepts

### Reporting dataset
A reporting dataset is a read-optimized structure derived from core operational tables.

### Export-ready view
An export-ready view is a shaped result used for spreadsheet exports or downloadable reports.

### Read model
A read model is a derived representation optimized for query performance and reporting use.

## Functional behavior

### Operational summaries
The module must support summary data for operational dashboards or management views.

### Export preparation
The module must support preparing data for export in structured formats.

### Cross-module reporting
The module must support reporting across records, organizations, access context, and configuration data.

### Future BI readiness
The module should keep the system compatible with future business intelligence expansion.

## Data ownership

The reporting support module should not own source-of-truth transactional tables.

It may own:
- reporting views.
- materialized views.
- export staging tables.
- read models if they are clearly derived and maintained by the reporting layer.

## Key validations

The module should validate:
- reporting filters are valid.
- access-aware reporting rules are respected.
- derived datasets are refreshed correctly.
- exports do not expose unauthorized data.

## API responsibilities

The module may expose APIs for:
- operational summaries.
- export generation.
- filtered report retrieval.
- dataset refresh or status endpoints if needed.

## Dependency boundaries

The module may depend on:
- record for record data.
- organization for organization-based summaries.
- people_access for access-aware reporting.
- admin_config for type and setting lookup.

The module should not implement business workflows or permission ownership.

## Reporting rules

- Reporting must respect access control.
- Reporting data should be derived from authoritative tables.
- Summaries should be consistent across environments.
- Sensitive fields must be excluded when unauthorized.

## Implementation notes

- Optimize for read performance without changing business ownership.
- Keep reporting logic isolated from transaction logic.
- Prefer derived data over duplicated manual syncs where possible.
- Make export formats predictable and versionable.
- Prepare for future BI expansion without forcing it into the core product.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `02-domain-model.md`
- `03-functional-requirements.md`
- `06-api-contracts.md`
- `07-data-model.md`
