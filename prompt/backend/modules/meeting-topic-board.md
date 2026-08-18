# Meeting Topic Board — Backend Logic

> **UI scope:** One primary operational screen — **Meeting → Topic** (`/meetings/topics`), 1+3 split board (`AppMeetingTopicBoard`).  
> **Record model:** `meeting-topic` and `meeting` are **record types** in the unified record module, not separate product domains.  
> **References:** `prompt/specification/modules/record.md` (meeting / meeting-topic), `prompt/frontend/00-product-ui-design-map.md` (split boards), `frontend/app/composables/meeting/useMeetingTopicBoard.ts` (current client contract).

---

## 1. Purpose

The Topic page is the **folder + card** workspace for meetings:

- **Left rail:** all **topics** (folders). Topics group meetings; they do **not** show a meeting date on the topic row/card in this view (title, status/stage/tags/summary only — no date slot on topic chrome).
- **Right pane:** **meeting cards** for the selected scope: All meetings, Unassigned (no topic), or one topic’s children.
- Users **create meetings**, optionally **auto-link to a topic**, or leave them **unassigned** until drag-and-drop assignment.
- Within a topic, meetings have a **stable user-defined order** (`sort_order`).
- Meetings may **recur** (loop); the system materializes or schedules occurrences according to recurrence rules.
- Each meeting has a **scheduled date-time** (and optional duration). When start time is **near**, the client promotes the card (top of list + border animation); the backend must expose enough data to compute that reliably.
- **Online** meetings expose a **join URL** on the card.
- **Notes** (rich text + attachments) belong to the meeting record; users may attach **Google Drive** files already synced in Portal (async pick, not re-upload).
- **Card visible fields** follow **App Config → Display → card fields** (`meetingHistory` / `meetingTopics` keys); API responses should include all fields needed for configured slots.

Meeting **History** (`/meetings/history`) may remain a table/archive route; **operational meeting work** on the Topic board is authoritative for assignment, order, notes, and imminent display.

---

## 2. Domain entities

Both entities map to `record` (+ `record_detail`, attachments, links) with fixed type codes (exact codes follow `record_type` configuration):

| Concept | Record type | Role |
| --- | --- | --- |
| **Topic** | `meeting-topic` | Folder/container; owns ordered child meetings via link |
| **Meeting** | `meeting` | Card in the board; optional `topic_id`; notes, time, URL, recurrence |

### 2.1 Topic (meeting-topic)

| Field / concept | Storage | Rules |
| --- | --- | --- |
| `id` | record id | Stable UUID |
| `title` | record.title | Required |
| `status`, `stage` | record | Lifecycle is only `active | archived | deleted`; configured workflow stage is separate |
| `description` | record_content or detail | Optional summary |
| `record_time` | record | Optional business time for search/timeline; **not shown as a date on Topic rail UI** |
| `child_meeting_count` | denormalized or computed | Count of linked meetings |
| `child_meetings` | optional embed on list/detail | Lightweight list: `{ id, title, meetingDate, sortOrder }` for topic document page only; board loads meetings via meeting list API |

Topics do **not** require `meetingDate` for the Topic board left rail.

### 2.2 Meeting (meeting)

| Field / concept | Storage | Rules |
| --- | --- | --- |
| `id` | record id | |
| `title` | record.title | Required |
| `topic_id` | record link or detail | Nullable — **unassigned** when null |
| `topic_title` | denormalized | Updated when `topic_id` changes |
| `sort_order` | detail integer | **Required when `topic_id` is set**; unique per topic; lower = higher in list |
| `meeting_date` | record_time or dedicated detail | **Scheduled start** (ISO 8601, timezone-aware) |
| `meeting_end` or `duration_minutes` | detail | Optional; used for “in progress” / overlap |
| `location` | detail | Physical or label “Online” |
| `meeting_mode` | detail enum | `in_person` \| `online` \| `hybrid` |
| `meeting_url` | detail URL | Required when mode is `online` or `hybrid`; validated URL; **shown on card** for one-click join |
| `notes` / `record_content` | record_content | TipTap HTML for meeting notes dialog |
| `recurrence` | detail JSON or child records | See §5 |
| `series_id` | detail | Links occurrences to one recurrence series |
| `is_recurrence_exception` | detail boolean | Skipped or one-off edit of a series instance |
| Letter / org fields | detail | Existing product fields (`letter_number`, participants, units, etc.) |
| Attachments | record_attachment | Files + Drive references (§7) |

Core record columns (`status`, `stage`, `record_tag`, `record_time`) remain available for cards and search.

Participant/assignee fields use arrays of `{ id, label, type }` references (`officer`, `department`, or `company`) and share the mention-search contract in `../00-integration-contract.md`. One selection and many selections use the same payload shape.

---

## 3. Topic board views (API support)

The client uses three meeting pools (query params on list endpoint):

| View | Query | Sort default |
| --- | --- | --- |
| **All** | no `topic_id` filter | `meeting_date` asc, then title |
| **Unassigned** | `topic_id=null` | same |
| **One topic** | `topic_id={uuid}` | **`sort_order` asc**, then `meeting_date` |

Topic list endpoint: paginated topics, optional search on title/owner; **no date filter on topic list** for this screen.

Meeting list endpoint: must support `topicId`, `unassignedOnly`, `startDate`, `endDate`, `q`, `limit`, `sort`. Path is `GET /api/v2/meetings/history` (never `/meetings`).

---

## 4. Assignment and ordering

### 4.1 Assign meeting to topic (drag-drop or menu)

**Operation:** `PATCH /api/v2/meetings/history/{id}` or `POST /api/v2/meetings/history/{id}/assign-topic`

Body:

```json
{
  "topicId": "uuid-or-null",
  "sortOrder": 0
}
```

Rules:

1. Setting `topicId` to `null` **unassigns**; clear or ignore `sort_order` for unassigned pool.
2. Assigning to a topic appends at end if `sortOrder` omitted: `max(sort_order for topic) + 1`.
3. **Idempotent:** same topic + same order → no-op success.
4. Update denormalized `topic_title` on meeting and refresh topic `child_meeting_count`.
5. Emit activity event: `meeting.topic_assigned` / `meeting.topic_unassigned`.
6. Permission: `meetings.assign_topic` (or edit on both meeting and topic).

### 4.2 Reorder within topic

**Operation:** `POST /api/v2/meetings/reorder` (batch) or multiple PATCHes in a transaction

Body:

```json
{
  "topicId": "uuid",
  "orderedMeetingIds": ["id1", "id2", "id3"]
}
```

Rules:

1. All ids must belong to `topicId`.
2. Persist `sort_order` = index in array (0-based).
3. Atomic transaction; on failure, no partial order.
4. Return updated meetings or 409 on concurrent reorder (optional ETag on topic).

Client today: `reorderMeeting` + `assignMeetingToTopic` in `useMeetingTopicBoard.ts`.

### 4.3 Create meeting with optional auto-topic

On **create**:

```json
{
  "title": "...",
  "meetingDate": "2026-08-10T14:00:00+07:00",
  "topicId": "optional-uuid",
  "meetingMode": "online",
  "meetingUrl": "https://..."
}
```

- If `topicId` present → set `sort_order` to end of topic.
- If omitted → meeting appears in **Unassigned** until user assigns.

Optional product rule: default topic from user preference or “current selected topic” is **UI-only**; backend stores explicit `topic_id` only.

---

## 5. Recurrence (loop meetings)

Meetings can belong to a **series** (`series_id`).

### 5.1 Recurrence rule (stored on series master or template meeting)

Example detail shape:

```json
{
  "frequency": "weekly",
  "interval": 1,
  "byWeekday": ["MO", "WE"],
  "until": "2026-12-31T23:59:59Z",
  "count": 52
}
```

Supported frequencies (minimum): `daily`, `weekly`, `monthly`. Exactly one of `until` or `count` should bound the series.

### 5.2 Occurrence materialization

Docetra uses **expand on write**: APScheduler publishes the recurrence-expansion job, and a RabbitMQ worker creates meeting rows for the next configured horizon (default 90 days). Each occurrence is a real record with its own notes, attachments, stage, date, and stable occurrence ID. Expand-on-read virtual occurrences are not used.

### 5.3 Editing series

- Edit **this occurrence only** → set `is_recurrence_exception` on instance; detach from auto-regeneration for that date.
- Edit **all future** → update rule + regenerate from cutoff date (job).
- Delete occurrence vs delete series — separate APIs with confirm semantics.

Required engine: APScheduler owns the `meeting_recurrence_expander` interval/cron schedule and publishes due work to RabbitMQ. It also owns one-off meeting reminders and start/end events. Full behavior is defined in `../02-meeting-scheduler.md`.

---

## 6. Imminent / “near meeting” behavior

**Product:** When `meeting_date` is within a configured window, the card should sort **to the top** of the current topic/pool view and show a **visible border animation** (client).

Backend responsibilities:

| Item | Behavior |
| --- | --- |
| `meeting_date` | Always return in ISO 8601 with offset |
| `imminent` (computed) | Boolean: `now <= meeting_date <= now + threshold` |
| `minutes_until_start` | Integer, signed (negative = started) |
| `in_progress` | Optional: `now` between start and end |
| Threshold | App Config: `meetings.imminentMinutesBefore` (default **15**) |

List endpoint should accept `sort=imminent_first,meeting_date` so server and client agree on ordering when multiple cards are imminent.

Optional: WebSocket or SSE `meeting.imminent` for desktop notifications (out of scope for MVP if client polls every 60s).

**Do not** rely only on client clock for audit; server computes `imminent` using server time in API responses.

---

## 7. Notes and attachments

### 7.1 Notes

- Persist rich text in `record_content` (HTML from TipTap).
- **Save:** `PATCH` meeting with `notes` / `recordContent`; validate size limits and sanitize HTML server-side.
- **History:** record module history tracks content changes (who/when); optional dedicated `meeting_note_revision` only if product requires full revision UI.

### 7.2 Attachments (upload)

Standard record attachments via storage module:

- `GET /api/v2/meetings/history/{id}/attachments`
- `PUT` or `POST` replace/upload (multipart or signed URL flow)

Metadata: `AttachmentMeta` (id, name, mime, size, url, source).

### 7.3 Google Drive async pick (Portal)

User selects files **already imported** via Google Drive Sync (Portal), not re-uploading from disk in the notes dialog.

Backend:

1. **Catalog endpoint:** `GET /api/v2/portal/drive-files?search=&page=` (permission: portal + meeting edit).
2. **Link to meeting:** `POST /api/v2/meetings/history/{id}/attachments/link`

```json
{
  "source": "google_drive",
  "driveFileId": "…",
  "driveSyncJobId": "optional",
  "displayName": "…"
}
```

3. Create `record_attachment` row pointing at stored file metadata (storage integration module); **no duplicate binary** if file already in Docetra storage.
4. Operation is **async-safe:** if Drive metadata sync is pending, return `202` + job id; client polls attachment status until `ready` or `failed`.

Permissions: user must have view on Drive file and edit on meeting.

---

## 8. Online meeting URL

| Rule | Detail |
| --- | --- |
| Field | `meeting_url` when `meeting_mode` ∈ `online`, `hybrid` |
| Validation | HTTPS preferred; block javascript: URLs |
| Card | Include in list/detail payload whenever mode is online/hybrid |
| Audit | Log URL changes in activity (no secret tokens in logs) |

---

## 9. App Config — card display

Settings **App Config → Display → card fields** (`display.cardFields.meetingHistory`, `display.cardFields.meetingTopics`, `display.cardFooterAlign`) are persisted in settings service.

Backend:

1. **GET** app config (existing settings API) includes display section.
2. Meeting/topic **list and detail** responses include **all scalar fields** referenced in `MEETING_CARD_SLOTS` / `TOPIC_CARD_SLOTS` (see `frontend/app/utils/card-fields.ts`) so the client can render any configured slot without N+1.
3. Optional: `GET /api/v2/settings/card-fields` public read for boards after auth (cached).

Topic board rule: **topic rail must not expose date slots** in default topic card config; backend still may store `record_time` for search.

---

## 10. API surface (aligned with frontend)

Under `/api/v2`. Do **not** publish `/meeting-topics` or `/meetings` as public aliases; the Nuxt adapters already call the paths below.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/meetings/topics` | Topic rail list |
| GET | `/meetings/topics/{id}` | Topic detail document |
| POST | `/meetings/topics` | Create topic |
| PATCH | `/meetings/topics/{id}` | Update topic |
| GET | `/meetings/history` | Board pools (filters §3) |
| GET | `/meetings/history/{id}` | Meeting detail + notes fields |
| POST | `/meetings/history` | Create (optional topicId, recurrence) |
| PATCH | `/meetings/history/{id}` | Update fields, topic, URL, notes |
| POST | `/meetings/reorder` | Batch order within topic |
| POST | `/meetings/history/{id}/assign-topic` | Shortcut assign/unassign |
| GET | `/meetings/history/{id}/attachments` | List attachments |
| POST | `/meetings/history/{id}/attachments` | Upload |
| POST | `/meetings/history/{id}/attachments/link` | Link Drive / existing file |
| DELETE | `/meetings/topics/{id}` | Permission-gated card-menu soft delete (`status=deleted`) |
| DELETE | `/meetings/history/{id}` | Permission-gated card-menu soft delete (`status=deleted`) |
| POST | `/meetings/topics/{id}/archive`, `/restore` | Owner-scoped archive/restore |
| POST | `/meetings/history/{id}/archive`, `/restore` | Archive pauses schedules; restore rebuilds eligible schedules |
| DELETE | `/meetings/topics/{id}/purge`, `/meetings/history/{id}/purge` | Administrator-only purge |

Shared entity sub-resources (`comments`, `activity`, `neighbors`, `favorite`, `counts`, `options`) follow [`06-backend-file-structure.md`](../06-backend-file-structure.md) §5.2.

Generic `/records?type=meeting` is an internal implementation option only. Public JSON and paths stay on `meetingTopics` / `meetingHistory`.

---

## 11. Permissions (minimum)

| Code | Use |
| --- | --- |
| `meetings.topics.view` | Topic rail |
| `meetings.topics.edit` | Create/update topic |
| `meetings.view` | List/read meetings on board |
| `meetings.edit` | Update meeting, notes, URL |
| `meetings.assign_topic` | Drag-drop assign/reorder |
| `meetings.notes.edit` | Save notes + attachments |
| `meetings.topics.delete` / `meetings.delete` | Delete from the card `⋯` menu |
| `portal.drive_files.view` | Pick Drive files for notes |

Enforce on every mutating route; frontend hides actions but backend is source of truth.

---

## 12. Activity and audit

Emit immutable activity events (for document-style timeline and record logs):

- `meeting.created`, `meeting.updated`
- `meeting.topic_assigned`, `meeting.topic_unassigned`, `meeting.reordered`
- `meeting.notes_updated`, `meeting.attachment_added`, `meeting.drive_file_linked`
- `meeting.recurrence_updated`
- `meeting.deleted`, `meeting_topic.deleted`
- `meeting.archived`, `meeting.restored`, `meeting.purged`
- `meeting.imminent` (optional, once per occurrence)

---

## 13. Validation summary

| Case | Validation |
| --- | --- |
| Assign to unknown topic | 404 |
| Reorder meeting not in topic | 422 |
| Online mode without URL | 422 on save (warn on draft) |
| `sort_order` gaps | Allowed; normalize on reorder |
| Recurrence without end bound | 422 |
| Drive link to file user cannot access | 403 |
| HTML notes | Sanitize; max length |

---

## 14. Frontend mapping (implementation checklist)

| UI behavior | Backend |
| --- | --- |
| Left rail topics, no date on topic | Topic list without date-driven sort; card config excludes date slots for `meetingTopics` |
| All / Unassigned / topic filters | `GET /meetings/history` query params |
| Drag card to topic | `assign-topic` + `sort_order` |
| Drag reorder in topic | `POST /meetings/reorder` |
| Border animation / top sort | `imminent`, `minutes_until_start`, sort param |
| Join link on card | `meeting_url`, `meeting_mode` |
| Open notes dialog | `GET/PATCH` meeting + attachments APIs |
| Uppy upload in notes | `POST` attachments |
| Delete topic/meeting from `⋯` | Confirm, authorize `.delete`, soft delete, remove card, emit audit event |
| Pick Google Drive file | `attachments/link` + Drive catalog |
| Card slots from settings | Full field payload + app config display |
| Create meeting | `POST /meetings/history` with optional `topicId` |

---

## 15. Out of scope (this document)

- Google Drive Sync job engine (see `prompt/frontend/17-portal-google-drive-sync.md`).
- Full Meeting History table UX (separate route; may share same meeting APIs).
- Calendar export (iCal) — future module.

---

## 16. Frontend contract (implemented — swap mock → HTTP)

When `NUXT_PUBLIC_USE_MOCK_DATA=false`, the UI calls the same paths as mock mode.

| Concern | Code |
| --- | --- |
| Shared API types | `frontend/app/types/docetra/meeting-api.ts` |
| Board sort / imminent (client fallback) | `frontend/app/utils/meeting/board.ts` |
| Assign, reorder, Drive catalog, link | `frontend/app/adapters/meeting-board.ts` |
| Endpoint constants | `frontend/app/utils/constants/api-endpoints.ts` |
| Topic board state | `frontend/app/composables/meeting/useMeetingTopicBoard.ts` |
| Meeting entity fields | `frontend/app/types/docetra/entities.ts` (`MeetingHistory`) |
| Document create prefill `?topicId=` | `frontend/app/composables/workspace/useDocumentPage.ts` |

### Endpoint map (must match backend)

| Operation | Method | Path |
| --- | --- | --- |
| List topics | GET | `/api/v2/meetings/topics` |
| List meetings | GET | `/api/v2/meetings/history` |
| Assign topic | POST | `/api/v2/meetings/history/{id}/assign-topic` |
| Reorder | POST | `/api/v2/meetings/reorder` |
| Drive catalog | GET | `/api/v2/portal/drive-files` |
| Link Drive file | POST | `/api/v2/meetings/history/{id}/attachments/link` |
| Attachments | GET/POST | `/api/v2/meetings/history/{id}/attachments` |

List/detail meeting payloads should include optional server fields: `imminent`, `minutesUntilStart`, `inProgress` (see `MeetingBoardTiming`). If omitted, the client computes timing from `meetingDate` + `durationMinutes`.

---

**Mock → HTTP:** `NUXT_PUBLIC_USE_MOCK_DATA=false`. Date filters use `startDate`/`endDate` ([`07-datetime-and-list-query.md`](../07-datetime-and-list-query.md)).

**Backend files (later):** `app/api/v2/meetings.py`, `app/modules/meetings/`, `app/scheduler_jobs/`.
