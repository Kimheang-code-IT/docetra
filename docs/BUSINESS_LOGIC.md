# Docetra — Business Logic

Cross-cutting rules verified in the implementation. Flow-specific details live in MEETING_FLOW.md / DOCUMENT_FLOW.md / ORGANIZATION.md / PORTAL.md / FILE_STORAGE.md / CONFIGURATION.md.

## Unified record engine

- Every business item is a **Record** typed by **RecordType**; behavior is type-driven, never hardcoded per screen.
- Built-in types auto-seed with UI defaults (`TYPE_UI_DEFAULTS` + `resolve_or_ensure_type`): `meeting_topic`, `meeting_history`, `document`, `incoming_document`, `outgoing_document`, `master_list_request`.
- Record rows carry `record_content`/`record_metadata` JSON plus dynamic attribute values in `record_detail`.
- **`record_time`** is configurable per type (priority list; first valid candidate wins), indexed, and sorts mixed timelines.
- Numbering: per-type prefixes generate reference numbers — INC (incoming), OUT (outgoing), DOC (document), MLR (master list), MTG (meeting), TPC (topic).

## Lifecycle (all entities)

```
active (status=1) → archived (status=2) → restore → active
active/archived → deleted (status=0, soft) → restore
deleted → purge (hard delete; permission-gated, deletable flag respected)
```

- Archive/restore/purge/bulk-delete are separate permission actions.
- `version` + `If-Match` on every mutation → 409 on conflict; the frontend reloads after conflict.
- Comments/activities attach to any entity; comments editable by author (`edited_at`).

## Workflow stages

- Per-type stage templates (`record_stage_template`); document types default to a 10-stage flow ending `finished_final` (isFinal); meetings use intake → review → approval → **completed** (isFinal).
- Stage transitions via `PATCH .../stage` require the `transition` action; invalid stages rejected.
- Completed meetings are excluded from active boards (`excludeStage=completed`) and remain in history.

## Topics & meetings

- `meeting_topic` is a record type with `supportsTopicContainer: true`; meetings store `topicId`, `topicTitle`, `sortOrder` in their payload.
- A meeting belongs to at most one topic; unassign = `topicId: null`.
- Topic ordering of children is explicit (`sortOrder` / reorder endpoint) — never hardcoded.
- Counts (total/unassigned/per-topic) come from a single `getGroupCounts` call.

## Documents

- Incoming/outgoing/master-list/document are separate record types sharing the same engine; the `document` type provides the **combined** view.
- Tracking fields: sender/recipient organization (`record_organization` links), received/sent dates, owner, assignee, waiting flag, reference number, document type tabs.
- Stage flow supports "waiting related document" and director/DDG/DG submission steps out of the box.

## Organizations

- `organization_type` distinguishes `department` | `company` (registry-driven; `_meta/types`).
- Hierarchy via `parent_id` (+ `child_ids`, `lvl`) — cycles rejected; a department may be a main department or sub-department.
- Sectors support their own parent hierarchy; purposes are flat.
- Companies reference `sector_id` + `organization_purpose_id` — reusable classifications.
- Officers bind to an organization and a role; `auth_id` optionally links a login account.

## Files & attachments

- Three layers: bytes (MinIO object) → `file` metadata row → `record_attachment` link.
- Upload endpoint writes real bytes; **no local-only fake references**.
- Detach removes only the link; File/object deletion is explicit and permission-gated.
- URL attachments: file metadata created without bytes; business link still exists.
- Upload validation: type allow-list, size ≤ `max_upload_size_mb` (25 default), storage target availability.

## Audit & notifications

- Significant mutations append to `audit_log` (action, table, row, ip, status, detail JSON).
- Notification delivery is transactional-outbox (`outbox`) → worker; `notification_audit_log` tracks processing.
- Meeting reminders scheduled in `meeting_schedules`, fired by the scheduler, delivered via Telegram/email integrations.
- Records expose `activity` (timeline) and `comments` endpoints consumed by the detail page.

## Search / Ask AI (honesty contract)

- `/search` is keyword-only and **reports itself as keyword** (`semanticAvailable: false`). No fake semantic mode.
- `/search/ask` returns `available: false` with real keyword citations — no fabricated answers.
- Mentions (`/mentions`) serve officer/department/company @mentions.

## Exports

- `POST /exports` creates a job (selected rows/fields/date bounds); worker generates CSV; result expires in 24h (`expiresAt`); scheduler purges expired exports. Status: queued → running → completed/failed; delete/cancel supported.

## Dashboard

- KPI list filtered by caller permissions; per-user Redis cache (short TTL) keyed by identity + permission fingerprint; stage distribution + records-over-time + meeting events.
