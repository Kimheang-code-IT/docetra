# Portal Module — Upload, Sync & Logs (Backend Logic)

> **UI scope:** Portal nav — **File Upload**, **Google Drive Sync**, **Logs**; Drive file catalog used from Meeting notes.  
> **References:** `prompt/specification/modules/storage-integration.md`, `prompt/frontend/17-portal-google-drive-sync.md`, `frontend/app/adapters/meeting-board.ts` (`PORTAL_DRIVE_FILES`).

---

## 1. Purpose

Portal is the **external file & sync** surface:

| Route | UI | Status |
| --- | --- | --- |
| `/portal/file-upload` | `AppFileUploadBoard` (1+3: Uppy left, table right) | Implemented |
| `/portal/google-drive-sync` | Generic `EntityWorkspaceView` | **Partial** — dedicated sync UI open |
| `/portal/portal-logs` | `EntityWorkspaceView` read-only | Implemented |
| `/api/v2/portal/drive-files` | Catalog for linking files to meetings/notes | Contract in meeting adapter |

Portal does **not** replace the storage module; it orchestrates uploads, sync jobs, and audit visibility.

---

## 2. Domain entities

### File upload item

Represents one uploaded file (or batch row) tracked in Portal.

| Field | Role |
| --- | --- |
| `id` | Primary key |
| `fileName`, `mimeType`, `sizeBytes` | Display |
| `status` | `pending` \| `uploading` \| `ready` \| `failed` |
| `storageProviderId` | From Settings → Storage |
| `uploadedBy`, `uploadedAt` | Audit |
| `entityLink` | Optional link to business record |

### Google Drive sync source / job

| Concept | Role |
| --- | --- |
| **Source** | Connection, folder id, schedule, last/next run |
| **Job** | One sync run: imported / skipped / failed counts, error summary |
| **Synced file** | Catalog row exposed as `drive-files` for pickers |

Secrets (tokens) stored encrypted; never returned in list/detail API.

### Portal log

Immutable operational events (upload, sync, link, permission change) — same pattern as record logs but scoped to portal actions.

---

## 3. File Upload flow

```text
User selects files (Uppy)
  → POST upload (multipart or signed URL from storage module)
  → Storage persists binary + metadata
  → Portal row created/updated (status ready)
  → Optional link to record_attachment
```

**Board APIs:**

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v2/portal/file-uploads` | Table (paginated, status filter, search) |
| GET | `/api/v2/portal/file-uploads/{id}` | Detail document |
| POST | `/api/v2/portal/file-uploads` | Register upload / complete callback |
| DELETE | `/api/v2/portal/file-uploads/{id}` | Remove when policy allows |

Upload endpoint on client today: `/api/v2/meetings/history/{id}/attachments` for meetings; portal uses entity-specific attachment routes from storage integration.

**1+3 UI rules:** Left panel hosts upload widget; right panel server-paginated table only — never load full history client-side.

The current uploader accepts a bounded configurable file count/size/type list and refuses to attach Authorization to a cross-origin endpoint. The API must still treat every client rule as advisory: resolve the authenticated tenant/user, enforce storage policy, inspect content instead of trusting extension or `Content-Type`, scan malware, generate a safe storage key, and return normalized `AttachmentMeta` only after acceptance.

---

## 4. Google Drive Sync flow (target)

See `prompt/frontend/17-portal-google-drive-sync.md` for UI. Backend should provide:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v2/portal/google-drive-sync` | Sources + jobs list (or split resources) |
| POST | `/api/v2/portal/google-drive-sync/sources` | Add source |
| POST | `/api/v2/portal/google-drive-sync/sources/{id}/sync` | Manual job (async) |
| GET | `/api/v2/portal/google-drive-sync/jobs/{id}` | Job status polling |

Jobs run **async**; API returns job id; client polls or subscribes to events. Long jobs must not block HTTP worker.

---

## 5. Drive file catalog (link picker)

Used when linking an already-synced file to a meeting note or record.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v2/portal/drive-files` | `search`, `page`, `limit` |
| POST | `/api/v2/meetings/history/{id}/attachments/link` | Link by `driveFileId` (see meeting module) |

Response shape: `DriveFileCatalogItem` in `frontend/app/types/docetra/meeting-api.ts`.

If file metadata still syncing → `202 Accepted` + job id; client polls attachment status.

---

## 6. Portal logs flow

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v2/portal/logs` | Paginated, read-only |
| GET | `/api/v2/portal/logs/{id}` | Event detail |

No comment composer; activity **is** the audit product.

---

## 7. Permissions

| Code | Use |
| --- | --- |
| `portal.file_upload.view` / `.edit` | Upload board |
| `portal.google_drive_sync.view` / `.edit` | Sync (when shipped) |
| `portal.logs.view` | Portal logs |
| `portal.drive_files.view` | Drive catalog picker |

---

## 8. Integration with Storage settings

- Active/default provider from **Settings → Storage** (`/api/v2/settings/storage`).
- Connection test before marking source active.
- File binary always via storage module APIs; Portal stores **business linkage** and **job state**.

---

## 9. Frontend contract

| Concern | Code |
| --- | --- |
| File upload board | `AppFileUploadBoard.vue` |
| Drive sync pages | `pages/portal/google-drive-sync/*` |
| Portal logs | `entityConfigs.portalLogs` |
| Endpoints | `api-endpoints.ts` → `FILE_UPLOADS`, `GOOGLE_DRIVE_SYNC`, `PORTAL_LOGS`, `PORTAL_DRIVE_FILES` |
| Link helper | `adapters/meeting-board.ts` → `listPortalDriveFiles`, `linkMeetingDriveFile` |

---

## 10. Validation & safety

| Rule | Enforcement |
| --- | --- |
| Max file size | Provider config + request rejection |
| Allowed MIME/types | Provider allow-list |
| Content validation | Server-side signature/MIME sniffing; reject SVG/active content where inline preview is possible |
| Malware | Quarantine and scan before status becomes `ready` |
| Upload origin | Signed URLs are issued only for approved storage origins; normal bearer uploads stay on the API origin |
| File names | Store an opaque key; sanitize display/download headers and prevent path traversal |
| Secrets in API responses | Strip always |
| Cross-tenant file access | 403 on link if user lacks file scope |

---

*Complete Drive Sync backend together with storage-integration module; until then mock `EntityWorkspaceView` remains valid.*
