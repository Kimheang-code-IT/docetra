# Docetra — System Flow (End-to-End)

High-level flows across frontend ↔ API ↔ services ↔ database ↔ storage/queue.

## Authentication flow

```
Login page → POST /auth/login → verify password_hash → issue JWT pair
  → HttpOnly cookies (docetra_session + docetra_refresh) + user payload
Frontend: store user (localStorage) → paint shell immediately
  → background GET /auth/me validates → 401 → POST /auth/refresh → retry
  → refresh fails → clearSession() → /auth/login (broadcast to tabs)
403 anywhere → permission toast, never logout. 429 → rate-limit feedback.
```

## App boot / navigation

```
Nuxt plugin → auth store (stored user) → useRecordSurfaces.load()
  → GET /records/_meta/surfaces (cached per identity, 7-day localStorage TTL, background revalidate)
  → menus + dynamic routes: /meetings/{typeCode}, /records/{typeCode}
Guard middleware → permission check per route (UX only)
```

## Topic → Meeting → Complete → History

```
/meetings/topics (useMeetingTopicBoard)
  → GET topics (list) + GET meetings (excludeStage=completed) + GET counts (one call)
Create topic → POST /records/meeting_topic
Create meeting → /meetings/history/new?topicId=… → POST /records/meeting_history
Drag assign → POST /records/meeting_history/{id}/assign-topic → refresh() (optimistic + rollback)
Reorder → POST /records/meeting_history/reorder {topicId, orderedMeetingIds}
Stage work → PATCH .../stage (intake → review → approval)
Complete → PATCH .../stage (completed) → excluded from board (excludeStage)
History → /meetings/history list + detail (timeline via .../activity)
Reminders → meeting_schedules → scheduler → outbox → Telegram/email
```

## Incoming / Outgoing document flow

```
/records/incoming-documents | outgoing-documents (EntityWorkspaceView)
  → GET list (q, page, limit, sort, status, stage, date range, waiting)
Create → new page (schema-driven form: GET /records/{type}/schema)
  → POST (numbering INC/OUT, required attributes validated)
Detail → EntityDocumentView: fields (AppDynamicFieldRenderer → record_detail),
         related records, files, comments/activity, permissions
Track → owner/assignee/waiting; stage drag → PATCH .../stage
        (created → … → waiting_related_document → director/DDG/DG → finished_final)
Attachments → multipart upload → File + RecordAttachment (or URL/Drive link)
Complete/Archive → archive endpoint → /archive (restore possible)
```

## Combined documents view

```
/records/documents (type `document`) → same dynamic API → one table across
incoming + outgoing + general documents (recordTypeName column distinguishes)
```

## Organization flow

```
/organizations/department | company (dynamic org router)
  → hierarchy (parentId) cycle-safe; company ← sectorId + purposeId (reusable catalogs)
Officer → organization + role; optional auth_id → user account
Mentions → GET /mentions → officer/department/company @mentions in meeting/document forms
Record links → record_organization (sender/recipient/participant units)
```

## File & Drive flow

```
Upload → POST /records/{type}/{id}/attachments/upload (multipart)
  → validate (type/size) → MinIO object → file row → record_attachment → 201
Download → GET /files/{file_id} (authorized stream)
Detach → DELETE .../attachments/{file_id} (link only; File survives)
Drive → /portal/google-drive-sync: source → sync → job queued
  → RabbitMQ → worker run_sync_job → file rows (source_table='drive-files')
  → poll jobs/{job_id} → completed/failed → /portal/drive-files → link to record
```

## Permission flow

```
Role editor → GET /users/permission-catalog (structured rows) → matrix save
  → PUT /users/roles/{id} {permissionRows:[{code, is_enable, scope}]}
Request → require_permission(prefix.action) → creator-scope filter (scope='creator')
  → 403 (no logout) or filtered results
Dashboard → per-user cache key (identity + permission fingerprint)
```

## Audit & logs flow

```
Mutation → service → DB write + audit_log append (action, table, row, ip, status)
        → activity row (entity timeline) + outbox event (notifications)
Views: /records/logs (record audit), /portal/portal-logs, /system-monitor/system-logs
  → canonical audit DTO → centralized frontend mappers
```

## Export flow

```
POST /exports {resource, selectedIds?, fields, dateFrom/To}
  → export job Entity (queued) → RabbitMQ consumer generate_export
  → CSV built from authoritative tables (access-aware) → expiresAt +24h
Frontend polls GET /exports/{id} with backoff → download link → DELETE to cancel/remove
Scheduler cleanup_expired_exports purges expired artifacts
```
