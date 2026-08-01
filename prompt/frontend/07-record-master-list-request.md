# Prompt 07 — Master List Request

## Copy/paste prompt

Implement `/records/master-list-requests` as a **Topic-style split board** (`AppRecordStageBoard`), same pattern as Incoming / Outgoing / Document.

### Board layout

- Left: stages rail with search, **All records**, stage cards + counts; collapsible to icon-only.
- Right: datepicker (`updatedAt`) + search; 3-column record cards (title, owner subtitle, date, status/stage).
- Drag onto a stage or `⋯` → Move to stage. Row actions: Detail · Logs · Delete.

Create → `/records/master-list-requests/new`; card → `/records/master-list-requests/:id`. The Nuxt UI document page renders configured attributes, related records, files, metadata rail, and Comments & Activity. Do not hardcode variable business fields; obtain them from record type/template metadata.

### Acceptance

Topic-style board is default; stage filter and drag-move work; collapse is icon-only; dynamic document fields still work; checks pass.
