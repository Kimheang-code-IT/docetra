# Prompt 25 — Document Type

## Copy/paste prompt

Implement `/configuration/document-types` as a reference and behavior configuration table.

Use server search/pagination and filters for direction applicability, enabled state, workflow mapping, and usage. Columns: stable code, localized name, direction, workflow/stage template, usage count, status, order, and updated time. No Kanban.

Add navigates to `/configuration/document-types/new`; rows navigate to `/configuration/document-types/:id`. The Nuxt UI document page supports direction rules, default workflow, allowed attributes, ordering, usage references, metadata, and immutable Configuration Activity. Referenced types must be disabled rather than hard-deleted; duplicate or invalid codes must map to field errors.

### Acceptance

Document type settings drive document forms and views, referenced values remain safe, activity is complete, and checks pass.
