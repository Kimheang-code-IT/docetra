# Prompt 10 — Company

## Copy/paste prompt

Implement `/organizations/companies` as a reusable organization workspace.

### Page design

Use a server table with optional compact card view, not Kanban. Search/filter by sector, purpose, status, parent organization, external-access state, and sharing activity. Columns/cards show identifier, company name, sector, purpose, contact, status, shared-record count, and updated time.

Add navigates to `/organizations/companies/new`; rows/cards navigate to `/organizations/companies/:id`. The Nuxt UI document page supports identifiers, localized name, hierarchy, sector, purpose, contacts, status, and external context. Tabs include Details, Relationships, Shared Records, Officers, and Access, with a metadata rail and Comments & Activity below the form. Activity tracks metadata, hierarchy, sharing, and external-access changes.

### Acceptance

Company data is server-paginated, external sharing remains backend-authorized, document history is complete, and checks pass.
