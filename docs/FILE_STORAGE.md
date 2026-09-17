# Docetra — File Storage

Verified implementation: `modules/storage_integration/services/storage.py|providers.py|provider_service.py|drive_sync.py`, `application/attachment_router.py`, `integrations/objectstore.py`, MinIO (S3 API).

## Three-layer attachment architecture

```
1. Storage file   — raw bytes in object storage (MinIO bucket `docetra`)
2. File metadata  — `file` row in PostgreSQL: nam, path, file_size, mime_type,
                    storage_type, direct_url, source_table, status
3. Record-attachment link — `record_attachment` (record_id, reference_id, file_id)
```

Storage concerns, metadata, and business linkage stay independently maintainable.

## Upload flow (record/meeting attachment)

```
Frontend multipart POST /records/{type}/{id}/attachments/upload
  → application/attachment_router (composition layer)
      1. permission check (edit action on resource)
      2. validation: type allow-list, size ≤ max_upload_size_mb (25 MB default), storage target available
      3. write bytes → object storage (shared/upload_validation.detect_upload_type)
      4. create `file` metadata row
      5. create `record_attachment` link
      → 201 { file payload + attachment }
```

- **No base64**; real bytes over multipart. No local-only fake references.
- URL attachments: metadata row without bytes (`direct_url` set), link created — business link exists without binary.

## Download

`GET /files/{file_id}` — current_user required; streams the object with filename + content type; 403 on unauthorized, 404 on missing.

## Detach vs delete

- `DELETE /records/{type}/{id}/attachments/{file_id}` removes **only the link** — the shared File and object remain (other records may reference it).
- File/object deletion happens only through explicit portal delete/purge flows, permission-gated, lifecycle-preserving (active → trash states).

## Storage providers (Settings → Storage)

- `POST/GET/PUT/PATCH/DELETE /settings/storage` — provider CRUD (S3-compatible endpoints, bucket, credentials).
- `POST /settings/storage/{id}/test-connection` — connectivity test.
- `POST /settings/storage/{id}/set-default` / `set-active` — default target + enable/disable.
- Credentials encrypted at rest (`settings_encryption_key`) and never returned in API responses (redaction).

## Google Drive files

- Synced Drive files are `file` rows with `source_table='drive-files'` (metadata + optional cached object); linked to records via the same `record_attachment` layer (`POST .../attachments/link`).

## Validation rules

- File type: allow-list check (`detect_upload_type`).
- Size: ≤ `max_upload_size_mb` (config, default 25).
- Storage target: default active provider must be reachable; test-connection endpoint for ops.
- Linked record references validated (`record` must exist and be active).

## Invariants

- Binary content **never** in PostgreSQL.
- Metadata always in PostgreSQL, created for every successful upload.
- Storage references stable and queryable (`path`, `direct_url`).
- Storage details do not leak into unrelated module logic (record module only consumes the public facade).
- Upload/sync operations auditable; permission validated before any file access.
