# Prompt 02 — Meeting Topic

## Copy/paste prompt

Implement `/meetings/topics` as a **split topic/meeting board** (not the generic workspace Kanban as the primary view). Keep `/meetings/topics/new` and `/meetings/topics/:id` on the shared ERP-style document page.

### Board layout (`AppMeetingTopicBoard`)

Use a responsive **4-column grid**:

- **1 column left** — title **Topic**, search under it (filter by topic name), **All topics** control, then scrollable topic cards.
- **3 columns right** — meetings title, datepicker + search, scrollable meeting cards.

### Behavior

- **Default:** right pane lists **all meetings** across topics (and unassigned).
- **Click a topic card:** right pane shows **only meetings for that topic**, ordered by `sortOrder` then date.
- **Open topic:** `⋯` → Open topic, or double-click the card → `/meetings/topics/:id`.
- Left: topic search. Right: meetings title, **datepicker** + search (no hint subtitle under the title).
- **Meeting card click:** navigate to `/meetings/history/:id`.
- **Order:** when a topic is selected, meetings can be **reordered by dragging** onto another meeting card.
- **Drag and drop:** drag a meeting onto a topic card to **assign** it. Highlight drop target.
- **Meeting card `⋯`:** Open meeting · Open notes · Assign to topic · Unassign.
- **Open notes:** fullscreen dialog (`AppMeetingNotesDialog`) — TipTap notes in **3 cols**, Uppy files in **1 col**; save updates `notes` + attachments on the meeting.
- Header Create → `/meetings/topics/new`; Refresh reloads topics + meetings.

### Data

- Topics: meeting topic adapter. Meetings: meeting history adapter (`topicId`, `topicTitle`, `sortOrder`).
- Assigning updates the meeting, then syncs the topic’s `childMeetingCount` / `childMeetings`.
- Enforce no-duplicate topic link (a meeting belongs to at most one topic).

### Document pages

Add Topic → `/meetings/topics/new`; topic document keeps Summary / Meetings tabs, metadata rail, Comments & Activity.

### Acceptance

Split board is the default topics index, filter-by-topic works, DnD assign and `⋯` assign work, ordered meetings reorder when a topic is selected, document routes still work, and checks pass.
