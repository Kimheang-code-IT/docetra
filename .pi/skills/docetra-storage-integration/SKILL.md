# docetra-storage-integration

## Purpose

Use when implementing or modifying file uploads, file metadata, object storage interaction, file status, Google Drive sync, or file-to-record linkage support.

## Source Documents

- docs/specification/modules/storage-integration.md
- docs/specification/modules/record.md (consumer of the three-layer attachment architecture)

## Domain Overview

The storage integration module manages file uploads, file metadata, object storage references, and Google Drive synchronization. It provides the storage layer for Docetra without mixing binary handling into business modules. It must not own business record logic or workflow logic.

## Key Entities

| Entity | Responsibility |
|---|---|
| File | Metadata representation of an uploaded or synchronized binary asset |
| Storage object | The actual binary asset stored in the configured object storage system |
| Sync source | External storage or folder source (e.g., Google Drive) used to import/synchronize file data |
| Record-attachment link | Relationship connecting a record to a file metadata record or another related record (business linkage layer — link table consumed with the record module) |

## Three-Layer Attachment Architecture (MUST preserve)

1. **Storage file** — the raw binary asset in object storage.
2. **File metadata** — persistent PostgreSQL record for EVERY uploaded file: file name, path, size, mime type, storage type, direct URL, status. This is the business-facing record of a stored asset.
3. **Record-attachment link** — relationship table connecting a record to file metadata (or another related record). Business linkage layer.

URL attachments: same three layers but SKIP upload — a file metadata record represents the URL, and a record-attachment link connects it to the business record. The link exists even without a binary file.

## Business Rules

- Binary content MUST be stored OUTSIDE the database.
- Metadata MUST be stored in PostgreSQL.
- Every successful upload MUST create a persistent file metadata record.
- Storage references MUST remain stable and queryable.
- Storage details MUST NOT leak into unrelated module logic.
- Upload and sync processes MUST be auditable where appropriate.
- Permission MUST be validated before allowing file access.
- Preserve file lifecycle state rather than deleting data aggressively (support active and trash-like states).
- Support future storage backends if required.
- Sync logic MUST be explicit and isolated.

## Permissions

- File retrieval and access require authorization (via people_access). Exact rules: `Needs verification`.

## State / Workflow Rules

- File status tracking: active and trash-like states where needed. Exact status values: `Needs verification`.
- Google Drive sync: trigger sync / track sync status from managed Google Drive locations when enabled. Exact job lifecycle: `Needs verification`.

## Implemented Behavior (verified in code)

- **Portal file management**: `/portal/file-upload` (+ [id]) with `AppFileUploadBoard`; `/portal/portal-logs` (+ [id]) for portal activity logs.
- **Google Drive sync**: `/portal/google-drive-sync` (+ new/[id]) with `AppGoogleDriveSync`; supports source creation, sync start, job polling, file refresh; `AppMeetingDriveFilePicker` links Drive files to meetings.

## API Rules

The module SHOULD expose APIs for:

- File upload.
- File metadata detail retrieval.
- File listing.
- File association with records.
- File status update.
- Sync trigger / sync status endpoints (where applicable).

Exact routes/payloads: `Needs verification`.

## Data Rules

- Module owns: `file`, plus any sync-state tables or external file reference tables introduced later.
- File metadata fields (per spec): file name, path, size, mime type, storage type, direct URL, status.
- Sync source configuration must be valid.

## Validation Rules

- File type MUST be allowed.
- File size MUST be within allowed limits.
- Storage target MUST be available.
- File metadata MUST be complete.
- Sync source configuration MUST be valid.
- Linked record references MUST be valid where applicable.

## Edge Cases

- URL "attachment" with no binary → create file metadata representing the URL + record-attachment link; no upload. (Explicit in spec.)
- Failed/incomplete upload → no complete file metadata record should exist for a failed upload ("every successful upload must create metadata" implies failed uploads must not present valid metadata). (Derived from specification.)
- Record linkage to a nonexistent record → rejected. (Derived from specification: "linked record references are valid".)

## Implementation Guidance

- Keep file metadata separate from record content.
- Do not let record/business modules touch object storage directly — they consume this module's linkage support.
- Keep sync logic isolated and explicit (Google Drive or future sources).
- Validate permissions before any file access.

## DO NOT

- DO NOT store binary content in PostgreSQL.
- DO NOT implement business workflow rules unrelated to storage in this module.
- DO NOT own record logic.
- DO NOT aggressively delete files (preserve lifecycle state).
- DO NOT expose file access without permission checks.

## Testing Checklist

- [ ] Upload stores binary in object storage (not the database).
- [ ] Every successful upload creates a complete file metadata record in PostgreSQL.
- [ ] Disallowed file type is rejected.
- [ ] Oversized file is rejected.
- [ ] Unauthorized user cannot retrieve a file.
- [ ] File status can track active/trash states.
- [ ] File can be associated with a record via the attachment link.
- [ ] Invalid linked record reference is rejected.
- [ ] URL attachment creates metadata + link without upload.
- [ ] Google Drive sync can be triggered and status tracked (when enabled).
- [ ] Invalid sync source configuration is rejected.

## Needs Verification

- Exact allowed file types and size limits.
- Exact file status values and transitions.
- Exact Google Drive sync job lifecycle and endpoints.
- Exact API contracts.
