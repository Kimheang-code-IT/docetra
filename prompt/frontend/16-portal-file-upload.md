# Prompt 16 — File Upload

## Copy/paste prompt

Implement `/portal/file-upload` in the existing Nuxt UI application. Follow the shared foundation and storage integration specification.

### Implement now

Create only the localized File Upload header, Portal breadcrumb, upload permission metadata, and placeholder card. Do not add a dropzone or upload mock.

### Future UI contract

The final page will support accessible drag/drop and file selection, allowed-type/size validation, bounded concurrent uploads, per-file progress, cancellation/retry, and clear success/failure results. Successful uploads create persistent file metadata and may link to a permitted record. Do not store binary content in Pinia or PostgreSQL-facing payloads. Use direct/object-storage upload flows when the API contract supports them.

### Acceptance

The scaffold contains no file input or request and is correctly linked under Portal.

