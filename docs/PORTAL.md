# Docetra — Portal (File Upload, Google Drive Sync, Logs)

Verified implementation: `modules/storage_integration/*` (backend), `/portal/*` pages, `AppFileUploadBoard`, `AppGoogleDriveSync`, `AppMeetingDriveFilePicker`.

## File Upload (`/portal/file-upload`)

- Lists all managed files: fileName, mimeType, sizeBytes, uploader, storageSource, linkedRecordTitle, createdAt.
- Detail: read-only metadata + status; actions: archive/restore/purge, comments, attachments, neighbors.
- Every upload creates a `file` metadata row (name, path, size, mime, storage_type, direct_url, source_table, status) with bytes in MinIO.
- Files link to records through `record_attachment` (three-layer architecture — see FILE_STORAGE.md).

## Google Drive Sync (`/portal/google-drive-sync`)

Flow:

```
Create source   POST /portal/google-drive-sync/sources       (name, folderName, status)
Start sync      POST /portal/google-drive-sync/sources/{id}/sync
                → job Entity created: { kind:'job', sourceId, status:'queued', attempts, createdAt }
Poll status     GET  /portal/google-drive-sync/jobs/{job_id}  (queued → running → completed|failed)
Completed       job payload: { status:'completed', fileCount, completedAt }
Failed          errorMessage recorded on source/job payload
Refresh files   GET /portal/drive-files                       (source_table='drive-files')
Link to record  POST /records/meeting_history/{id}/attachments/link   (Drive file picker)
```

- Frontend page: source list (name, folderName, status, filesSynced, lastSyncAt, errorMessage), create dialog, sync trigger, job polling with completion/failed states.
- Worker executes `run_sync_job` (never the API process): lists the configured Drive folder via the Google integration, creates `file` rows, updates job payload.
- Retry: start a new sync for a failed/completed source (attempts tracked; `find_drive_job` matches only `queued|processing`, so re-sync works; worker retries up to `job_max_retries` then marks failed).

## Portal Logs (`/portal/portal-logs`)

- Read-only audit of portal operations: occurredAt, action, actor, target, summary.
- Backend canonical audit DTO mapped centrally in the frontend (`utils/audit/audit-dto.ts` → `auditToPortalView`).
- Detail view: action, summary, target, occurredAt (readOnly), plus comments/attachments/neighbors where applicable.

## Permissions

| Resource | Actions |
|---|---|
| portal.file_upload | view, create, delete, share, export |
| portal.google_drive_sync | CONFIG (view, create, edit, delete, export, comment) |
| portal.logs | AUDIT (view, export) |

## Rules

- Uploads validate file type + size (≤25 MB default) before storage writes.
- File access requires authorization (`GET /files/{file_id}`).
- Sync runs only in the worker; API only creates/queries jobs.
- Preserve file lifecycle (active → trash/archive) — no aggressive deletion.
- Sync state and drive files are Entity-table resources with the same versioned envelope semantics.
