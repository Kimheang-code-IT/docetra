# Prompt 23 — Record Type

## Copy/paste prompt

Implement `/configuration/record-types` as the control plane for record behavior.

Use a server table, not Kanban. Filters: search, enabled state, workflow-enabled, attribute count, and usage. Columns: stable code, localized label, description, workflow flag, stage count, attribute count, usage count, status, and updated time.

Add navigates to `/configuration/record-types/new`; rows navigate to `/configuration/record-types/:id`. The Nuxt UI document page includes identity, behavior flags, stage template editor, attribute/template mapping, card/table summary-field selection, validation preview, affected records, metadata, and immutable Configuration Activity. Do not add casual comments. Prevent code changes after adoption and prefer disable over deletion.

### Acceptance

Configuration drives later record pages, stage and attribute mappings validate, changes are auditable, and checks pass.
