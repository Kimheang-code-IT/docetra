# Prompt 04 — Incoming Document

## Copy/paste prompt

Implement `/records/incoming-documents` as a **Topic-style split board** (`AppRecordStageBoard`), not the plain table/Kanban workspace as the primary index.

### Board layout

**Left (stages rail)**

- Title **Stages**, search stages, **All records (n)** control.
- Stage cards with count badges (Intake / Review / Approval / Completed).
- Collapse to icon-only rail (Logs-style) so the cards gain width.
- Drag a record card onto a stage to move workflow stage.

**Right (records)**

- Collapse toggle + selected stage / All records title.
- Datepicker (`receivedDate`) + search.
- 3-column card grid (topic page style): title, sender subtitle, date, reference, status/stage badges, `⋯` (Detail · Logs · Move to stage · Delete).

Create → `/records/incoming-documents/new`; card click → `/records/incoming-documents/:id`. Document page keeps schema tabs, metadata rail, Comments & Activity.

### Acceptance

Split board is default; stage filter and drag-move work; collapse is icon-only; document routes still work; checks pass.
