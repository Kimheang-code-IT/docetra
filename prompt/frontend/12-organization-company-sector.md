# Prompt 12 — Company Sector

## Copy/paste prompt

Implement `/organizations/company-sectors` with the shared reference-data table and Nuxt UI document page.

Provide search, parent sector, status, usage, and ordering filters. Columns show stable code, localized label, optional parent, description, status, usage count, order, and updated time. Support a lazy hierarchy preview if sectors are nested; do not use Kanban.

Add navigates to `/organizations/company-sectors/new`; rows navigate to `/organizations/company-sectors/:id`. The document page handles create/detail/edit, referenced companies, hierarchy metadata, and immutable Configuration Activity. Prevent cycles and hard deletion of referenced sectors.

### Acceptance

Hierarchy and references are safe, table operations are server-backed, activity is permission-aware, and checks pass.
