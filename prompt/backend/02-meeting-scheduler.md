# APScheduler Meeting Scheduling Contract

APScheduler is the required scheduling engine for meeting timers, reminders, recurrence expansion, and schedule reconciliation. It decides **when** work becomes due. It does not replace RabbitMQ or execute slow business work inside the scheduler process.

## 1. Runtime boundary

```text
Meeting API transaction → PostgreSQL meeting/outbox
                         → upsert/remove APScheduler schedule

APScheduler due time → publish small RabbitMQ message → worker side effect
                                                  ├─ reminder/notification
                                                  ├─ recurrence expansion
                                                  ├─ meeting event/projection
                                                  └─ cache/search invalidation
```

Run APScheduler in the dedicated `scheduler` container using `python -m app.scheduler`. Do not start an independent scheduler inside every API or worker process. Local development runs one scheduler. Production begins with one active scheduler; high availability is allowed only after configuring a shared persistent data store/event coordination and unique scheduler identities supported by the selected APScheduler version.

Pin APScheduler in the backend dependency lockfile. Do not mix 3.x and 4.x examples or APIs; upgrading the major version requires migration and scheduler recovery tests.

## 2. Persistence and authority

- PostgreSQL meeting/recurrence data is the business source of truth.
- APScheduler uses a persistent PostgreSQL-backed job/schedule store. Never use the in-memory store outside isolated tests.
- Use stable schedule IDs so restarts and repeated API calls replace rather than duplicate schedules.
- Suggested ID: `meeting:{tenantId}:{meetingId}:{purpose}:{occurrenceId}`.
- Schedule arguments contain only identifiers and safe metadata, never secrets or full meeting records.
- Persist a mapping containing meeting ID, schedule ID, purpose, next run time, version, and last synchronization result for support/audit.
- A periodic reconciler compares active meetings with APScheduler schedules and repairs missing, stale, or orphaned entries.

## 3. Required schedules

| Purpose | Trigger | Result |
| --- | --- | --- |
| Meeting reminder | One-off date trigger for each configured offset | Publish `meeting.reminder.due` for Telegram Bot 1 and other enabled channels |
| Meeting start | One-off date trigger | Publish `meeting.started` projection/event; do not set lifecycle to Completed |
| Meeting end | Optional one-off trigger when duration/end exists | Publish `meeting.ended` projection/event; lifecycle remains separate |
| Recurrence expansion | Interval/cron maintenance schedule | Materialize the rolling recurrence horizon |
| Reconciliation | Every 15 minutes by default | Repair schedules from PostgreSQL truth |
| Cleanup | Daily maintenance | Remove expired scheduler results/orphans according to retention |

Reminder offsets are centrally configured, defaulting to 24 hours, 60 minutes, and 15 minutes. A user/meeting preference may narrow these values but cannot create an unbounded number of timers.

## 4. Create, update, archive, and delete

### Create

After the meeting transaction commits, upsert start/end/reminder schedules using the committed meeting version. Creating the same schedule again must be idempotent.

### Update

When date, time, timezone, duration, recurrence, or reminder preferences change, replace the affected schedules and remove obsolete ones. A due message contains the expected meeting version; the worker discards or safely recomputes stale messages.

### Archive/delete/cancel

Pause or remove all future schedules after commit. Already-published RabbitMQ messages remain safe because the worker reloads the meeting and confirms it is still active and eligible before any side effect.

### Restore

Rebuild only future eligible schedules. Do not send reminders whose intended run time is already outside the allowed misfire window.

## 5. Timezone and daylight-saving rules

- Persist instants in UTC and meeting timezone as a valid IANA identifier.
- Build triggers from the meeting's configured timezone, then persist/compare UTC instants.
- Never use the scheduler host's local timezone; `SCHEDULER_TIMEZONE=UTC` is mandatory.
- Reject nonexistent local wall times or require the user to choose a valid time.
- For ambiguous daylight-saving times, require/store the chosen offset so the occurrence is deterministic.
- Changing application default timezone does not silently move existing meetings; only meetings explicitly configured to inherit that setting may be recalculated under an approved migration.

## 6. Misfires, coalescing, and concurrency

- Default misfire grace is 5 minutes. Per-purpose policy may be stricter or wider.
- Coalesce repeated missed maintenance runs into the latest single run.
- A late reminder outside its grace window is recorded as skipped; it is not delivered hours later.
- Limit each meeting/purpose task to one concurrently running instance.
- Add small jitter only to maintenance/reconciliation work, never to an exact meeting start or user-facing reminder time.
- Scheduler callbacks must be short: validate identifiers, publish a persistent RabbitMQ message with publisher confirmation, record the result, and return.

## 7. RabbitMQ handoff

Publish to durable queues defined in `01-cache-and-messaging.md`. Every message includes `eventId`, `scheduleId`, tenant, meeting/occurrence ID, meeting version, purpose, intended fire time, actual publish time, correlation ID, and schema version.

Workers provide at-least-once safety through idempotency, reload current PostgreSQL state, enforce tenant and eligibility checks, and acknowledge only after durable completion. Notification retry/dead-letter policy belongs to RabbitMQ workers, not APScheduler.

## 8. API and frontend contract

Meeting create/update responses include normalized scheduling information:

```json
{
  "data": {
    "id": "meeting_123",
    "meetingDate": "2026-09-20T02:00:00Z",
    "timezone": "Asia/Bangkok",
    "reminderOffsetsMinutes": [1440, 60, 15],
    "nextScheduledActionAt": "2026-09-19T02:00:00Z",
    "scheduleState": "scheduled"
  }
}
```

Allowed scheduling states are `scheduled`, `paused`, `syncing`, and `error`; this operational state is separate from the business lifecycle `active | archived | deleted`. The frontend displays schedule errors to authorized users and offers a permission-gated retry/resync action; it never calculates or registers authoritative timers in the browser.

## 9. Observability and operations

Monitor scheduler heartbeat, next run time, schedule count, due/late/missed executions, reconciliation repairs, publish latency/failures, duplicate suppression, and clock drift. Alert when heartbeat is absent, schedule lag exceeds the configured grace, reconciliation repeatedly repairs the same item, PostgreSQL/RabbitMQ is unavailable, or host time is unsynchronized.

Use graceful shutdown so the scheduler stops acquiring work, finishes the current short publish callback, and releases ownership. Back up persistent schedule data with PostgreSQL, but always retain the ability to rebuild all meeting schedules from business tables.

## 10. Verification

- Create, edit, cancel, archive, restore, and delete scheduling tests.
- Restart recovery with a persistent store and no duplicate reminder.
- Misfire/coalescing/concurrency tests.
- IANA timezone, DST gap, DST overlap, and application-timezone-change tests.
- Stale meeting-version and already-published-message tests.
- RabbitMQ outage, publisher-confirm failure, reconciliation, and dead-letter tests.
- Multi-instance test before enabling production scheduler high availability.

Reference: [APScheduler user guide](https://apscheduler.readthedocs.io/en/master/userguide.html).
