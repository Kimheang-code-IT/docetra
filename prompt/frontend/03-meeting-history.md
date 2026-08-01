# Prompt 03 — Meeting History

## Copy/paste prompt

Implement the Meeting History workspace at `/meetings/history`, plus **per-meeting notes** that can be opened from the topic board.

### List workspace

Use `AppServerTable` with an optional timeline-view toggle, not Kanban. Filter by date range, meeting/topic, status, stage, actor, department, organization, and action. Columns include record time, meeting, topic, action, previous/new state summary, actor, and organization.

Rows support:

- Row click → `/meetings/history/:id`
- Per-row `⋯` (`AppRowActionsMenu`): View detail · View logs · Delete (when permitted)

Document page `/meetings/history/:id` uses sticky header, summary fields, metadata rail, attachments, and activity. Use cursor pagination because history can grow while the user is browsing.

### Meeting notes (TipTap + Uppy)

From the Meeting Topics board (`⋯` → **Open notes**), open `AppMeetingNotesDialog` (fullscreen `UModal`) for that meeting:

- Layout: **3-column editor** + **1-column files** (`lg:grid-cols-4`).
- Header: meeting title left, date + close right (no description block).
- **Notes:** `AppRichTextNote` — Nuxt UI `UEditor` (TipTap) with HTML content, sticky toolbar (undo/redo, headings, lists, marks, color, highlight, align, link, image, zoom). Persist on `MeetingHistory.notes`.
- **Files:** `AppUppyUploader` — Uppy Dashboard + XHR upload (mock uploader when `useMockData`). Support large files (up to 200 MB). Persist via adapter `listAttachments` / `replaceAttachments` and update `attachmentCount`.
- Save/cancel with unsaved-change confirm. Toast on success/failure.

Shared components live under `components/common/` (`AppRichTextNote`, `AppUppyUploader`) so other entities can reuse them later.

### Acceptance

History list/detail work; row actions work; notes dialog opens from the board; rich text and Uppy uploads save against the meeting; checks pass.
