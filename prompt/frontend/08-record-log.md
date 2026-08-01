# Prompt 08 — Record Logs

## Copy/paste prompt

Implement `/records/logs` as a read-only record audit explorer titled **Logs**.

### Index — split board (`AppRecordLogBoard`)

Do **not** use the plain `EntityWorkspaceView` table as the primary index. Use a **1+3 split** (same family as Meeting Topics):

**Left (1 col) — Log views**

- Header title **Log views** only (no subtitle). Comfortable padding (`px-4 py-3.5`).
- Vertical tabs with icon, label, and count, for example:
  - All events
  - Created / Updated / Stage changed / Shared
  - Incoming document / Outgoing document
  - Errors
- Each tab sets a filter and a **different column set** for the right table.
- Collapse control on the right toolbar toggles the left rail to **icon-only** (sidebar style, ~`3.5rem`) so the table gains width. Tooltips on icons when collapsed.
- Always side-by-side with the table — never stack the tab list above the table on desktop.

**Right (3 cols) — dynamic table**

- Toolbar: collapse toggle + active tab title on the left; **datepicker** + **search** on the right (same row; no subtitle under the title). Padding `px-4 py-3.5`.
- `AppServerTable` with columns driven by the selected tab (badges for action / severity / entity type; formatted datetimes).
- No row selection, no meta heart column, no create/delete.
- Per-row `⋯` via `AppRowActionsMenu`: View detail · View logs (opens event or related context).
- Row click / Detail → `/records/logs/:id`.
- Persist selected tab in URL (`?tab=`).

Composable: `useRecordLogBoard`. i18n under `docetra.recordLogBoard.*`.

### Detail — `/records/logs/:id`

Read-only Nuxt UI event page with schema tabs (Event / Linked record / Context): event summary, safe changes summary, request/correlation context, linked record, metadata rail, related activity. No Kanban, Add, Edit, Delete, or comment composition.

Escape event content and redact private fields, tokens, storage URLs, and backend-only payloads.

### Acceptance

Split board is default for Logs; tabs change columns; collapse is icon-only; date/search filter; detail page is permission-aware and redacted; checks pass.
