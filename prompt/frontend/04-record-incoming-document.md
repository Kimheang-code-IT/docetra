# Prompt 04 — Incoming Document

## Copy/paste prompt

Implement `/records/incoming-documents` for Docetra using the existing Nuxt UI frontend. Follow the shared foundation and record/document workflow specifications.

### Implement now

Create the localized Incoming Document header, Record breadcrumb, route/permission metadata, and shared blank placeholder only. Do not build a table, filters, detail drawer, or create form.

### Future UI contract

The full page will manage incoming document records with server-side search, pagination, sorting, date range, sender organization, owner department, document type, status, workflow stage, waiting state, and attachment indicators. Row actions must be permission-driven. Detail and edit experiences should load on demand, preserve history, and link to file metadata without placing binary data in record responses.

### Acceptance

The route is linked under Record, starts no API work, and passes project checks.

