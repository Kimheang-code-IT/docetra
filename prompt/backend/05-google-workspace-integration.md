# Google Workspace Integration — Future-Ready Contract

Google support is optional and disabled by default. It is implemented through backend provider adapters so the existing frontend pages do not depend directly on Google SDKs. Initial scope covers Google Sign-In, Calendar, Drive, and optional Gmail delivery; each capability can be enabled independently.

## 1. Capability rollout

| Capability | Purpose | Default |
| --- | --- | --- |
| Google Sign-In | Link a verified Google identity to an existing Docetra user or allow approved-domain sign-in | Off |
| Google Calendar | Create/update/cancel a calendar event for a Docetra meeting and import provider updates according to policy | Off |
| Google Drive | Import/synchronize approved folders and link synchronized files to meetings/documents | Existing API-ready feature, off until configured |
| Gmail API | Optional email-provider adapter for reset/security mail; SMTP or another transactional provider remains supported | Off |

Enabling one capability does not silently enable another or request broader OAuth scopes.

## 2. OAuth and account-linking model

- Use OAuth 2.0 authorization-code flow with PKCE and a server-side callback.
- Generate one-time `state` and nonce values, bind them to the initiating session, validate the exact redirect URI, and expire them quickly.
- Store access/refresh tokens encrypted in backend secret storage; never return them to the browser, logs, or App Config APIs.
- Request incremental least-privilege scopes and record the granted scopes, Google subject ID, Workspace domain, token expiry, connection owner, and revocation status.
- Google Sign-In resolves identity by immutable Google `sub`, never display name. Email matching may link only after verified-email, domain, collision, and administrator-policy checks.
- Disabling or unlinking Google revokes tokens where possible, stops future jobs, and records immutable activity. It does not delete Docetra records.
- Service accounts/domain-wide delegation are separate administrator choices for organization-owned Calendar/Drive access and require explicit Workspace administrator approval.

## 3. Calendar and meeting logic

Docetra remains authoritative for meeting business state, permissions, comments, activity, lifecycle, and APScheduler reminders. Google Calendar is an external projection.

```text
Meeting commit
  → transactional outbox
  → RabbitMQ google.calendar command
  → idempotent Google worker
  → Calendar event mapping + sync status
  → activity/audit + optional Telegram notification
```

- Create a Calendar event only when Google sync is enabled for that meeting and an authorized calendar/destination is selected.
- Store `meetingId`, Google calendar ID, event ID, provider version/etag, last synchronized version, status, and last safe error.
- Meeting update, reschedule, archive, soft delete, restore, and purge publish versioned synchronization commands after commit.
- Archive/soft delete cancels or marks the Google event according to configured policy. Restore recreates or restores it idempotently. Admin purge removes the mapping only after the provider cleanup reaches a terminal state or an administrator accepts a recorded orphan.
- APScheduler still owns reminder timing. Google reminders may be optionally disabled to avoid duplicate alerts with Telegram.
- Incoming Google changes arrive through verified push notifications plus periodic reconciliation. The backend fetches the event using stored identity; webhook payloads alone are never trusted.
- Conflict policy is configurable: `docetra_wins`, `google_wins_for_time_location`, or `manual_review`. Default is `docetra_wins`.
- Attendees receive only information they may view. Confidential notes, attachments, internal comments, and private attendee data are excluded.

## 4. Drive and document logic

- Reuse the existing Portal Drive synchronization and file-catalog contracts.
- Allow only administrator-approved Shared Drives/folders and permission-scoped user connections.
- Store Google file ID, drive ID, version/checksum, MIME type, owner/source connection, sync state, and Docetra file mapping.
- Workers are idempotent, virus-scan imported binaries, validate MIME/size, and avoid duplicate storage objects.
- Removing Google access marks the source disconnected; linked Docetra metadata remains available according to retention policy, while inaccessible provider content is clearly identified.
- Archive/delete/purge of a Docetra document does not delete the source Google file unless a separately authorized, explicitly configured ownership policy permits it.

## 5. Gmail provider logic

Gmail may implement the existing `EmailProvider` interface for development or an approved Workspace deployment. Forgot-password keeps the same uniform response, hashed single-use token, short expiry, rate limit, and session-revocation rules. The browser never chooses an arbitrary sender or recipient. Production volume should use an approved transactional delivery option with quotas and monitoring.

## 6. API and UI-ready contract

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v2/integrations/google/capabilities` | Return enabled features and safe connection status |
| POST | `/api/v2/integrations/google/connections/start` | Start scoped OAuth/PKCE connection flow |
| GET | `/api/v2/integrations/google/callback` | Server-side OAuth callback |
| DELETE | `/api/v2/integrations/google/connections/{id}` | Revoke/unlink connection |
| GET | `/api/v2/integrations/google/calendars` | List authorized calendar options |
| POST | `/api/v2/meetings/history/{id}/google-calendar/sync` | Enable or reconcile meeting event sync (optional; default off) |
| DELETE | `/api/v2/meetings/history/{id}/google-calendar/sync` | Disable meeting projection without deleting meeting |
| GET | `/api/v2/integrations/google/sync-jobs/{id}` | Read bounded job status |

Future UI settings expose only safe values: enabled capabilities, masked account/domain, connection health, last sync, approved calendars/folders, conflict policy, duplicate-reminder policy, and connect/revoke/test actions. Per-user preferences may choose an approved calendar and whether their own eligible meetings sync. Secrets and raw provider errors are never rendered.

Permissions:

- `integrations.google.view` — view safe status.
- `integrations.google.connect` — link/unlink own allowed account.
- `integrations.google.configure` — configure domains, service accounts, allowlists, policies, and organization connections.
- Meeting/document `.edit` plus resource visibility is required before selecting or synchronizing an external destination.

## 7. Reliability, cache, and observability

- RabbitMQ routes: `integrations.google.calendar`, `integrations.google.drive`, `integrations.google.email`, and their dead-letter routes.
- Use stable idempotency keys, manual acknowledgement, exponential retry with jitter, provider quota handling, and reconciliation jobs.
- Cache safe calendar/folder option lists briefly and stable capability/configuration metadata longer; keys include tenant, connection, user, and permission scope.
- Measure queued/succeeded/failed/retried/dead-lettered jobs, provider latency/quota, token refresh failures, webhook lag, conflicts, and oldest unsynchronized change.
- Send serious token, webhook, quota, or reconciliation failures to the private IT Telegram alert group without including user data or tokens.

## 8. Security and acceptance tests

Test OAuth state/nonce/PKCE, redirect allowlisting, verified domain enforcement, account collision, token encryption/rotation/revocation, incremental scopes, cross-tenant isolation, permission removal before delivery, webhook authenticity/replay, Calendar conflict policies, duplicate commands, quota/429/5xx behavior, Drive MIME/malware rules, lifecycle restoration, dead-letter recovery, cache isolation, and audit redaction.

No Google feature is production-ready until its Google Cloud project, consent screen, redirect URIs, scopes, data-retention disclosure, privacy policy, quota alerts, and credential rotation procedure are approved for the target environment.

## 9. Frontend contract

Default off. Drive catalog used today: `GET /api/v2/portal/drive-files`. Meeting attach: `POST /api/v2/meetings/history/{id}/attachments/link`.

| Concern | Code |
| --- | --- |
| Drive picker | `frontend/app/adapters/meeting-board.ts` |
| Sync jobs UI | `frontend/app/pages/portal/google-drive-sync/*` |
