# Prompt 24 — Record Attribute

## Copy/paste prompt

Implement `/configuration/record-attributes` as a schema-field management table.

Use server pagination and filters for datatype, required, enabled, visibility, and record-type usage. Columns: stable code, localized label, datatype, required, validation summary, visibility, usage count, status, and updated time. No Kanban.

Add navigates to `/configuration/record-attributes/new`; rows navigate to `/configuration/record-attributes/:id`. The Nuxt UI document page supports datatype, options/reference source, defaults, validation, visibility, formatting, record-type mappings, a live field preview, metadata rail, and immutable Configuration Activity. Block or explicitly migrate datatype changes that would invalidate stored values.

### Acceptance

All supported dynamic field types preview correctly, risky changes are guarded, activity is auditable, and checks pass.
