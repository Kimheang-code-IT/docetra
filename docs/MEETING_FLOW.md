# Docetra — Meeting Flow (Topic → Meeting → Complete → History)

Verified implementation: `useMeetingTopicBoard.ts` / `AppMeetingTopicBoard.vue` (frontend), `services/meeting.py`, `records/meeting_*` endpoints (backend).

## Model

- `meeting_topic` — container record type (`supportsTopicContainer: true`), stages like any record.
- `meeting_history` — the meeting record type; stages: **intake → review → approval → completed** (completed = final).
- Topic linkage stored on the meeting payload: `topicId`, `topicTitle`, `sortOrder`.

## End-to-end flow

```
1. Create topic            POST /records/meeting_topic            (title, description, recordTime, status=active)
2. Create meeting          POST /records/meeting_history          (letterNumber, title, letterDate, meetingDate,
                                                                    meetingMode, location/URL, durationMinutes,
                                                                    participants[], internalUnits[], externalUnits[],
                                                                    topicId? — pre-set when created from a topic)
                           UI: /meetings/history/new?returnTo=/meetings/topics&topicId=…
3. Assign meeting → topic  POST /records/meeting_history/{id}/assign-topic
                           { topicId, topicTitle, sortOrder }     (drag & drop; inactive topic → error toast)
   Unassign                same endpoint with topicId: null       (drop on Unassigned rail row)
4. Reorder inside topic    POST /records/meeting_history/reorder  { topicId, orderedMeetingIds }
5. Work the meeting        stage transitions via PATCH .../stage  (intake → review → approval)
6. Complete                PATCH .../stage → completed            (UI "complete" action)
7. History                 board excludes completed (excludeStage); meeting remains in /meetings/history
```

## Board behavior (topics page)

- **Topic rail**: search + paginated (30/page, `sort=-updatedAt`), includes archived topics so Activate stays available; counts per topic from `GET counts/groupBy` (`{ total, unassigned, groups }`).
- **Views**: All meetings (`selectedTopicId=null`) — full card list + search/date filter, sort by `meetingDate`; Unassigned pool (`__unassigned__` → query `topicId=__empty__`); per-topic — sort by `sortOrder`.
- **Meetings query**: `excludeStage=completed`, `q`, `startDate`/`endDate`, pagination (limit 20).
- **Card**: summary fields (letter number, subject, date, mode, location, participants, units, tags).
- **Optimistic assign**: local update → API → refresh; rollback + error toast on failure.
- **Topic management**: rename (concurrency token), archive/activate, delete.

## Rules

- MUST NOT allow assigning to an inactive/archived topic — **enforced server-side** (`_resolve_topic`: 422 invalid/archived/wrong-type, 404 missing/deleted).
- MUST NOT duplicate a meeting visually in standalone + container (assign removes from standalone pool by `topicId` scoping).
- Child order is configured (`sortOrder`), never hardcoded.
- Completed meetings never reappear on the working board.
- `assign` permission guards assign-topic and reorder actions.

## Meeting extras

- **Reminders**: `meeting_schedules` rows (job_key, run_at, kind, status) created per meeting; scheduler `due_meeting_reminders` fires; delivery via Telegram bot / email through outbox.
- **Drive files**: `POST .../attachments/link` links a synced Drive file to a meeting (`AppMeetingDriveFilePicker`); standard upload/detach flow also available.
- **Notes**: `AppMeetingNotesDialog` edits meeting notes (record content).
- **History timeline**: `AppMeetingHistoryTimeline` renders the meeting's activity feed (`GET .../activity`).

## Invariants

- One topic per meeting.
- Deleting a topic does not delete child meetings — the backend **detaches** them (`parent_record` + `topicId` details cleared), so they surface in the Unassigned pool.
- All changes audited; concurrent edits rejected via `If-Match`.
