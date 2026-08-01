# Prompt 05 — Outgoing Document

## Copy/paste prompt

Implement `/records/outgoing-documents` as a **Topic-style split board** (`AppRecordStageBoard`), same pattern as Incoming Document.

### Board layout

- Left: stages rail with search, All records, stage cards + counts; collapsible to icon-only.
- Right: datepicker (`sentDate`) + search; 3-column record cards (title, recipient subtitle, date, status/stage).
- Drag onto stage or `⋯` → Move to stage. Row actions: Detail · Logs · Delete.

Create → `/records/outgoing-documents/new`; card → `/records/outgoing-documents/:id` with shared Nuxt UI document shell (Details, Recipients, Relationships, Files, Delivery, Access; Comments & Activity).

### Acceptance

Topic-style board is default; recipient/workflow behavior stays distinct from incoming; collapse works; checks pass.
