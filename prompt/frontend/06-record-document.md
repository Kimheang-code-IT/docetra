# Prompt 06 — Document

## Copy/paste prompt

Implement the unified document explorer at `/records/documents` as a **Topic-style split board** (`AppRecordStageBoard`).

### Board layout

- Left: stages rail (All + Intake/Review/Approval/Completed) with counts; collapsible icon-only.
- Right: datepicker (`updatedAt`) + search; 3-column cards (title, document type subtitle, date, status/stage).
- Drag/move stage; `⋯` Detail · Logs · Delete.

Add → `/records/documents/new`; cards open the canonical source document route. The Nuxt UI document page selects direction/type and loads the correct schema. Do not duplicate incoming/outgoing source records.

### Acceptance

Topic-style board is default; type-driven detail still works; collapse works; checks pass.
