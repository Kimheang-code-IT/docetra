# Prompt 16 — File Upload

## Copy/paste prompt

Implement `/portal/file-upload` as a **1+3 split board** (`AppFileUploadBoard`), same family as Record Logs and Meeting Topics.

### Index layout

**Left (upload folder) — Uppy**

- Header title **Upload** only (comfortable padding `px-4 py-3.5`).
- Body: reusable `AppUppyUploader` (TipTap/Uppy stack already in the app) filling the panel height (`fill`).
- Collapse toggle (like Logs): left rail shrinks to **icon-only** (~`3.5rem`) with folder/upload icons and tooltips so the table gains width.
- Always side-by-side with the table — never stack the uploader above the table on desktop.
- On complete: create portal file-upload rows via adapter, toast, refresh table. Do not store binaries in Pinia.

**Right (uploaded files) — table**

- Toolbar: collapse toggle + **Uploaded files** title; search on the right.
- `AppServerTable` with file name, type, size, uploader, status, storage, linked record, uploaded date.
- Per-row `⋯` (`AppRowActionsMenu`): View detail · View logs · Delete (when permitted).
- Row click / Detail → `/portal/file-upload/:id`.

Persist left collapse in `useState`. i18n under `docetra.fileUploadBoard.*`.

### Detail — `/portal/file-upload/:id`

Read-only Nuxt UI document page with metadata rail, safe preview/download, record links, storage status, and immutable file Activity. Comments optional and off by default.

### Acceptance

Split board is default; Uppy uploads land in the table; collapse is icon-only; large history stays server-paginated; checks pass.
