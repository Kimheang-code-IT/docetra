# Docetra v2 Module: Storage Integration

## Purpose

The storage integration module manages file uploads, file metadata, object storage references, and Google Drive synchronization. It provides the storage layer support required by Docetra v2 without mixing binary handling into business modules.

## Module responsibilities

The storage integration module owns:
- file metadata.
- upload processing.
- object storage interaction.
- direct file URLs or storage pointers.
- storage status tracking.
- Google Drive import or sync behavior.
- file-to-record linkage support where storage-specific behavior is needed.

## Core concepts

### File
A file is the metadata representation of an uploaded or synchronized binary asset.

### Storage object
A storage object is the actual binary asset stored in the configured object storage system.

### Sync source
A sync source is an external storage or folder source, such as Google Drive, used to import or synchronize file data.

## Functional behavior

### File upload
The module must support uploading files into the configured object storage.

### File metadata creation
Every successful upload must create a persistent file metadata record.

### File retrieval
The module must support retrieving file metadata and storage references for authorized users.

### File status
The module must support file status tracking, including active and trash-like states where needed.

### Google Drive sync
The module must support synchronization or import from managed Google Drive locations when enabled.

### File linkage
The module must support linking files to records or other business entities through approved relationships.

## Data ownership

The storage integration module should own or primarily manage:
- `file`
- any sync-state tables or external file reference tables introduced later.

The module should not own business record logic or workflow logic.

## Key validations

The module should validate:
- file type is allowed.
- file size is within allowed limits.
- storage target is available.
- file metadata is complete.
- sync source configuration is valid.
- linked record references are valid where applicable.

## API responsibilities

The module should expose APIs for:
- file upload.
- file metadata detail retrieval.
- file listing.
- file association with records.
- file status update.
- sync trigger or sync status endpoints where applicable.

## Dependency boundaries

The module may depend on:
- record for record attachment or record file linkage.
- people_access for permission checks.
- admin_config for storage configuration values.
- reporting_support for export or file inventory reporting if needed.

The module should not contain business workflow rules unrelated to storage.

## Attachment and link architecture

Attachments are separated into three layers to keep storage concerns independent from business linkage:

### Storage file
The actual binary asset stored in object storage. This is the raw file content managed by the storage system.

### File metadata
The persistent metadata record created in PostgreSQL for every uploaded file. It tracks file name, path, size, mime type, storage type, direct URL, and status. This is the business-facing record of a stored asset.

### Record-attachment link
The relationship table that connects a record to a file metadata record or to another related record. This is the business linkage layer.

### URL attachments
URL attachments follow the same three-layer pattern but skip the upload step. A file metadata record is created to represent the URL, and a record-attachment link is created to connect it to the business record. The business record still needs a link even when there is no binary file.

This separation ensures that storage concerns, metadata management, and business record linkage remain independently maintainable.

## Storage rules

- Binary content must be stored outside the database.
- Metadata must be stored in PostgreSQL.
- Storage references must remain stable and queryable.
- Upload and sync processes must be auditable where appropriate.
- Storage details should not leak into unrelated module logic.

## Implementation notes

- Keep file metadata separate from record content.
- Support future storage backends if required.
- Make sync logic explicit and isolated.
- Validate permission before allowing file access.
- Preserve file lifecycle state rather than deleting data aggressively.

## Related documents

- `00-overview.md`
- `01-system-architecture.md`
- `02-domain-model.md`
- `03-functional-requirements.md`
- `04-permissions-and-access.md`
- `07-data-model.md`
- `modules/record.md`
