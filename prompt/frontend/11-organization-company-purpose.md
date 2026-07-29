# Prompt 11 — Company Purpose

## Copy/paste prompt

Implement `/organizations/company-purposes` as a blank scaffold in the existing Nuxt UI application.

### Implement now

Create the localized Company Purpose header, Organization breadcrumb, permission metadata, and placeholder card only.

### Future UI contract

This reference-data page will manage stable purpose codes, localized labels, description, status, usage count, sort order, and history. Use a server-paginated table even if the initial dataset is small. Prevent destructive removal when referenced; prefer disable/archive behavior. Forms must enforce unique stable codes, with validation errors returned by the API mapped to fields.

### Acceptance

The route is reachable from Organization, makes no request, and passes type/build checks.

