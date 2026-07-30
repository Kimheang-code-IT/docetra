# Prompt 11 — Company Purpose

## Copy/paste prompt

Implement `/organizations/company-purposes` as a reference-data table workspace.

Use `AppServerTable` with search, status, usage, and sort-order filters. Columns: stable code, localized label, description, status, usage count, order, updated by/time. Do not add Kanban.

Add navigates to `/organizations/company-purposes/new`; rows navigate to `/organizations/company-purposes/:id`. Use the Nuxt UI document page for create/detail/edit, referenced companies, metadata, and read-only Configuration Activity. Omit casual comments unless product owners explicitly enable them. Prevent hard deletion when referenced; provide disable/archive with confirmation.

### Acceptance

Codes are unique/stable, referenced values cannot be destructively removed, activity is auditable, and checks pass.
