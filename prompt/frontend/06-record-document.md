# Prompt 06 — Document

## Copy/paste prompt

Implement the unified document explorer at `/records/documents`.

### Page design

Provide a server table and optional Kanban view when the selected document type has configured workflow stages. Filters: direction, document type, organization, department, owner, status, stage, date range, attachment presence, and sharing scope. Persist view and filters in the URL.

Use shared summary rows/cards. Add navigates to `/records/documents/new`; rows/cards navigate to the canonical source document route. The Nuxt UI document page lets the user select direction/type and loads the correct schema. Tabs include Details, Workflow, Organizations, Relationships, Files, and Access, with Comments & Activity below the form. Do not duplicate incoming/outgoing source records.

When mixed types have incompatible stages, disable Kanban with an explanatory message or require a single type filter.

### Acceptance

The unified view remains type-driven, links to the same source records as specialized pages, handles mixed-stage constraints, and checks pass.
