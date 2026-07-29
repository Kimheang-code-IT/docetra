# Prompt 25 — Document Type

## Copy/paste prompt

Implement `/configuration/document-types` in the existing Nuxt 4, TypeScript, and Nuxt UI 4 frontend. Follow the shared foundation, administrative configuration module, and document requirements.

### Implement now

Create only the localized Document Type header, Configuration breadcrumb, route/permission metadata, and shared blank placeholder. Do not build a table, create/edit form, mock data, or API calls.

### Future UI contract

The complete page will manage document classifications using stable code, localized name, description, direction applicability, status, ordering, usage count, and audit history. Use server-side pagination, sorting, search, and status/direction filters. Referenced document types must be disabled rather than hard-deleted, and backend validation must prevent duplicate or invalid codes.

### Acceptance

The route appears under Configuration > Document Type, renders without business data or API work, and passes the production build.

