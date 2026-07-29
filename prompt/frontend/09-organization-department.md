# Prompt 09 — Department

## Copy/paste prompt

Implement `/organizations/departments` using the existing Nuxt UI stack and organization module rules.

### Implement now

Create only the localized Department header, Organization breadcrumb, route/permission metadata, and placeholder card. Do not create hierarchy widgets, tables, or forms yet.

### Future UI contract

The completed page will manage department records and cycle-safe parent/child hierarchy. Provide server-side search/pagination for large directories, status filtering, lazy child loading for the hierarchy, create/edit forms, and history. Parent selection must prevent self-reference and cycles, with backend validation authoritative. Department identifiers used by records and access control must remain stable.

### Acceptance

The route is present under Organization and contains no mock or live data.

