# Prompt 05 — Outgoing Document

## Copy/paste prompt

Implement `/records/outgoing-documents` in the existing Nuxt UI application, following the shared foundation and record module.

### Implement now

Add only a localized Outgoing Document header, Record breadcrumb, typed route/permission metadata, and placeholder card. No mock rows, forms, or requests.

### Future UI contract

The completed page will manage outgoing document records with server pagination/sorting/search and filters for recipient organization, owner department, type, sent date, status, stage, and waiting state. It will support permission-aware create/edit/share/export actions, attachment metadata, and record history. Bulk operations must operate on explicit IDs or a server-side selection token, never an implicitly loaded full dataset.

### Acceptance

The route renders correctly, sidebar state is correct, and the scaffold is data-free.

