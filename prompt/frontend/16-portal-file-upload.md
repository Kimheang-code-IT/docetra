# Prompt 16 — File Upload

## Copy/paste prompt

Implement `/portal/file-upload` using the shared upload, table, Nuxt UI document-page, attachment, and activity patterns.

### Page design

Top section: accessible drag/drop zone and file picker with allowed type/size guidance. Below: server-paginated upload table filtered by file name/type, uploader, status, linked record, storage source, and date.

Support bounded concurrent uploads, per-file progress, cancellation, retry, and partial failures. Clicking a file navigates to `/portal/file-upload/:id`, a read-only document page with metadata rail, safe preview/download, record links, storage status, and immutable file Activity. Comments are optional and disabled by default.

Do not store binary content in Pinia or database payloads. Use object-storage/direct upload contracts when available.

### Acceptance

Upload progress and retry are accessible, metadata persists separately from binaries, the table handles large history, and checks pass.
