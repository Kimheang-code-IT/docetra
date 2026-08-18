# Date, Time, Timezone, and List Query Contract

This contract makes backend datetime behavior match the **already-shipped frontend**. Pages format dates; the API stores and filters them.

**Frontend sources:**

| File | Role |
| --- | --- |
| `frontend/app/utils/date-picker.ts` | Parse/serialize picker values |
| `frontend/app/utils/date-time-range.ts` | Inclusive range at minute precision |
| `frontend/app/types/docetra/common.ts` `ListQuery` | `startDate`, `endDate` |
| `frontend/app/mocks/query.ts` | Mock list filter order of date fields |
| `frontend/app/composables/settings/useAppLocalization.ts` | Display formatting from App Config |
| `frontend/app/components/common/AppDateRangeFilter.vue` | Toolbar/export date range UI |

Related product rules: `00-integration-contract.md` §6, `02-meeting-scheduler.md` §5, `modules/settings-application.md` (locale/timezone), `modules/configuration-record-metadata.md` (`recordTimePriority`).

---

## 1. Storage vs display

| Layer | Rule |
| --- | --- |
| PostgreSQL timestamps | `timestamptz`, stored as UTC instants |
| Date-only business fields | `date` (no time) when the field type is `date` |
| API JSON | ISO 8601 strings |
| Meeting scheduled start | Instant in UTC **plus** IANA `timezone` on the meeting |
| Scheduler clock | `SCHEDULER_TIMEZONE=UTC` always |
| Browser | Formats with App Config `locale`, `timezone`, `dateFormat`, `timeFormat`, `firstDayOfWeek` |

Never persist a display-formatted string (`18/08/2026`, `Aug 18, 2026`). Never use the API host's local timezone for business values.

Changing App Config timezone does **not** rewrite existing `record_time` or meeting instants. Only meetings that inherit the default timezone may be recalculated under an approved migration (`02-meeting-scheduler.md`).

---

## 2. JSON shapes the frontend already sends and shows

### 2.1 Instant (datetime)

Examples the mock data and adapters already use:

- `2026-08-18T01:30:00.000Z`
- `2026-08-18T08:30:00+07:00`

The API should **accept** offset or `Z` forms and **return** UTC with `Z` (or a consistent offset). Do not return naive datetimes without offset.

Pydantic: parse to timezone-aware UTC. Reject unknown offsets only if they are malformed, not because they differ from App Config timezone.

### 2.2 Date-only

`YYYY-MM-DD`, example `2026-08-18`.

Used for letter/received/sent/document dates when the field type is `date`. Incoming create currently copies `recordTime` date (first 10 chars) into `receivedDate` on the client; the API must still validate and store the canonical field.

### 2.3 Datetime-local picker payload

`AppDateRangeFilter` / `serializePickerValue` emit:

- Date-only: `2026-08-18`
- Date-time: `2026-08-18T08:30` (no seconds, no offset)

List query `startDate` / `endDate` may arrive in **either** form. The backend must normalize before comparison (see §4).

Do not require the client to convert picker values to UTC. Interpret datetime-local strings in the **App Config IANA timezone** (or the meeting's timezone for meeting filters), then compare as UTC instants.

---

## 3. Canonical business time (`record_time`)

Product identity field: `recordTime` in JSON, `record_time` in PostgreSQL.

Resolution order is configured per record type (`recordTimePriority`). Typical fallbacks already used in UI/mocks:

| Kind | Preferred source |
| --- | --- |
| Meeting | `meetingDate` (scheduled start) |
| Incoming | `receivedDate` then `recordTime` |
| Outgoing | `sentDate` then `recordTime` |
| Document | `documentDate` then `recordTime` |
| Topic | optional `recordTime` (not shown on Topic rail chrome) |
| Logs | `occurredAt` |
| Archive row | `deletedAt` \|\| `archivedAt` \|\| `updatedAt` \|\| `createdAt` |

Keep `record_time` indexed. Mixed timelines (search, dashboard, archive) sort on the resolved value.

Lifecycle `createdAt` / `updatedAt` / `archivedAt` / `deletedAt` / `occurredAt` are audit instants, not substitutes for `record_time` on operational boards.

---

## 4. List and export range filters

`ListQuery` fields:

```ts
startDate?: string
endDate?: string
```

Frontend toolbars pass these on:

- Meeting topic board
- Record stage boards
- Record logs
- Entity workspace date filters
- Export jobs (`CreateExportJobInput.startDate` / `endDate`)

### Inclusive bounds (match `date-time-range.ts`)

Normalize to **minute precision**:

| Input | Start bound | End bound |
| --- | --- | --- |
| `2026-08-18T08:30` | `2026-08-18T08:30` | `2026-08-18T08:30` |
| `2026-08-18` | `2026-08-18T00:00` | `2026-08-18T23:59` |
| empty | open | open |

A row matches when its comparable instant is `>= start` and `<= end`.

Which column to compare (same order as `frontend/app/mocks/query.ts`):

```text
receivedDate || sentDate || meetingDate || occurredAt || updatedAt || createdAt
```

Prefer the **resolved `record_time`** for record/meeting collections. Use `occurredAt` for logs. Use archive timestamps for `/archive` client aggregation until a dedicated archive API exists.

Apply permission/tenant filters **before** counting and pagination. Date filters never leak rows the user cannot view.

---

## 5. Meeting schedule times

Meetings are not “date labels”; they drive APScheduler.

On write:

1. Persist `meeting_date` as UTC instant.
2. Persist IANA `timezone` (default from App Config).
3. Persist duration or end if provided.
4. After commit, upsert reminder / start / end schedules.

On read, the frontend may show `timezone`, `reminderOffsetsMinutes`, `nextScheduledActionAt`, `scheduleState`. Browser timers are presentation only.

Wall-clock rules (`02-meeting-scheduler.md`):

- Reject nonexistent DST times or require the user to pick a valid time.
- For ambiguous DST times, store the chosen offset.
- Reminder offsets default to 1440, 60, and 15 minutes.

Imminent-card highlighting is computed from the scheduled instant vs now; the API must return a reliable `meetingDate` / `recordTime`.

---

## 6. App Config localization fields

`GET/PATCH /settings/app-config` owns:

| Field | Validation |
| --- | --- |
| `defaultLanguage`, `availableLanguages` | `en`, `km` (extend only with i18n files) |
| `locale` | BCP 47 |
| `timezone` | IANA, e.g. `Asia/Phnom_Penh` |
| `dateFormat`, `timeFormat` | supported tokens only |
| `firstDayOfWeek` | `0`–`6` |
| `numberFormat`, `currency` | known identifiers |
| `meetingReminderOffsetsMinutes` | bounded list |
| `meetingRecurrenceHorizonDays` | positive bound (default 90) |

The frontend formats numbers/dates from these values. Endpoints must not hard-code Khmer/English formats.

---

## 7. Pagination and sort (travel with date filters)

Same query object as dates:

| Param | Contract |
| --- | --- |
| `page` | 1-based |
| `limit` | bounded; UI allows 10/20/50/100 and “All” — cap “All” server-side |
| `q` | indexed text search |
| `sort` | `-updatedAt` style; `-` = descending |
| `stage`, `status` | comma-separated; default list omits archived/deleted |
| `view` | `table` \| `kanban` \| … (hint only; do not change authorization) |

`sort=-recordTime` must use the resolved business time.

---

## 8. Tests

- Date-only range includes the full local day in App Config timezone.
- Datetime-local `T08:30` is not treated as UTC unless the string has `Z`/offset.
- Meeting create in `Asia/Phnom_Penh` stores the correct UTC instant and scheduler trigger.
- DST gap/overlap cases on meeting write.
- Log/board filters do not return out-of-range or unauthorized rows.
- Export jobs reuse the same `startDate`/`endDate` semantics as the list they came from.
