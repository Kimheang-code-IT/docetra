# Notifications and Third-Party Integrations

Docetra uses provider adapters and RabbitMQ workers for external delivery. The API never waits synchronously for Telegram or email providers, and a third-party outage must not block core record or meeting transactions.

## 1. Integration map

| Channel | Audience | Required purpose |
| --- | --- | --- |
| Telegram Bot 1 — Meeting Alerts | Authorized Docetra users | Meeting reminders, reschedules, cancellations, and imminent-meeting alerts |
| Third-party email provider | Docetra account owner | Forgot-password/reset email and security notices |
| Telegram Bot 2 — Development Monitor | Private development/operations chat | Deployments, application version, code/config/docs updates, CI/CD failures, health incidents, queue/scheduler alerts |

The two Telegram bots must use different tokens, allowlisted chat IDs, permissions, message templates, queues/routing keys, and rate limits. Never reuse the development bot for end-user meeting content.

## 2. Delivery architecture

```text
APScheduler / API / CI webhook / monitoring rule
                 → PostgreSQL outbox + notification record
                 → RabbitMQ routing key
                 → notification worker
                 → Telegram Bot API or email provider
                 → delivery attempt/status/audit
```

Persist provider-neutral notification intent before publishing. Workers deliver at least once, so each provider request uses a stable idempotency/deduplication key. Store safe delivery status and provider message ID; never store provider tokens or complete password-reset URLs in logs.

Recommended RabbitMQ routes:

- `notifications.telegram.meeting`
- `notifications.telegram.devops`
- `notifications.email.security`
- `notifications.dead_letter`

## 3. Telegram Bot 1 — meeting notifications

APScheduler publishes due reminders according to `02-meeting-scheduler.md`. The worker reloads the current meeting, verifies it is active, checks the expected version, resolves eligible recipients, applies each user's language/timezone preference, and sends only to verified Telegram chat mappings.

Supported events:

- Reminder at configured offsets, default 24 hours, 60 minutes, and 15 minutes.
- Meeting date/time, location, mode, or join-link change.
- Meeting cancellation, archive, or deletion.
- Optional imminent/start notification when enabled.

Messages may include title, formatted time/timezone, location/mode, safe internal link, and a validated HTTPS join link. Do not include confidential notes, attachments, attendee directories, session links, or fields the recipient cannot view. Recheck meeting permission at delivery time.

Users link Telegram through a short-lived, one-time verification challenge. Store chat ID encrypted or access-controlled, record verification time, permit unlink/revoke, and reject unsolicited bot commands by default. Bot commands, if later enabled, are allowlisted and authorization-checked against the linked Docetra identity.

Meeting notifications may target a verified user chat or an administrator-approved Telegram group. A group destination stores a stable internal destination ID, masked Telegram chat identifier, display name, verification state, enabled event types, and allowed organization/department scope. Administrators verify and allowlist groups; meeting editors may select only destinations permitted for that meeting. Before sending, the worker rechecks meeting visibility and excludes confidential fields. Group membership is controlled by Telegram, so sensitive meetings must use direct verified recipients or a dedicated restricted group.

## 4. Forgot-password email provider

`POST /api/v2/auth/forgot-password` always returns the same accepted response whether or not the account exists. Apply per-IP and per-normalized-account rate limits, abuse monitoring, and optional CAPTCHA/risk controls.

For an eligible account:

1. Generate a cryptographically random single-use token.
2. Store only its hash with user, purpose, creation, expiry, and consumed/revoked state.
3. Build an HTTPS reset URL using the configured frontend origin; never accept a caller-supplied redirect host.
4. Publish `notifications.email.security` through the transactional outbox.
5. The provider adapter sends a templated reset message. Default expiry is 15 minutes.
6. `POST /api/v2/auth/reset-password` validates token hash, expiry, purpose, and one-time use; changes the password; revokes all active sessions; and emits an immutable security audit event.

Support SMTP initially behind an `EmailProvider` interface. Additional transactional email APIs may be added without changing auth services. Provider credentials are secret-manager values, not App Config fields or API response data.

## 5. Telegram Bot 2 — development monitoring

Bot 2 posts only to private allowlisted development/operations groups. Each IT destination has allowed environments, repositories/services, event classes, and minimum severity. Accepted sources are authenticated internal monitoring events and signed CI/CD webhooks—not arbitrary browser requests.

Event classes:

- Deployment started/succeeded/failed and rollback.
- Application version promoted, including environment and release link.
- Backend/frontend code revision deployed, with repository, branch/tag, commit ID, and safe summary.
- Documentation revision published, with changed document group and commit/link.
- CI build/test/security scan result.
- API health degradation, elevated error rate/latency, database/cache availability.
- RabbitMQ backlog/dead letters and worker failure.
- APScheduler heartbeat absence, misfire, or reconciliation failure.
- Storage/Drive sync and backup failure.

Every inbound development event requires HMAC signature validation, timestamp/replay protection, schema validation, source allowlisting, and rate limiting. Messages contain no secrets, diffs, user data, raw exception dumps, environment variables, reset links, or access tokens. Link only to access-controlled CI, logs, or monitoring pages.

Severity routing:

| Severity | Behavior |
| --- | --- |
| Info | Version, docs, successful deployment; grouped to reduce noise |
| Warning | Degraded dependency, growing queue, repeated retry; send once then update/thread |
| Critical | Failed production deployment, outage, data/security risk; immediate alert and recovery update |

## 6. Reliability and failure behavior

- Use publisher confirms, manual acknowledgements, exponential retry with jitter, and dead-letter routing.
- Retry `429` using provider `Retry-After`; retry safe `5xx`/network errors; do not retry permanent invalid recipient/chat errors indefinitely.
- Apply circuit breakers and per-provider concurrency/rate limits.
- Meeting/email failures appear in an authorized notification-delivery view; development failures alert through another monitored channel when Telegram itself is unavailable.
- A notification can be cancelled before delivery when its meeting/version is obsolete.
- Provider outage never rolls back the originating business transaction.

## 7. UI customization and secrets

Configuration is layered so it can be customized safely from the UI later:

| Scope | Editable values | Required permission |
| --- | --- | --- |
| Administrator/App Config | Enable each bot, verify/allowlist destinations, event-to-group routing, templates, default reminder offsets, escalation policy, quiet-hour defaults | `settings.app_config.configure` |
| Meeting | Select approved group(s), reminder offsets within policy, and whether update/cancel alerts are enabled | meeting `.edit` plus destination scope |
| User preference | Opt in/out by allowed event/channel, personal reminder offsets, quiet hours, timezone, and language | authenticated self-service |
| IT routing | Environment/service filters, minimum severity, grouping/dedup window, and recovery messages | administrator/operations configure |

Shipped frontend test routes (do not replace): `POST /api/v2/settings/app-config/email/test-connection`, `.../email/send-test`, `.../telegram/test-connection`, `.../telegram/send-test`. Optional later split paths may add `/telegram/meeting|devops/...`. Meeting payloads reference internal destination IDs, never Telegram chat IDs.

App Config may expose non-secret templates, enabled event types, reminder offsets, quiet-hour policy, and safe sender display names. Bot tokens, SMTP/API credentials, webhook secrets, and provider signing keys live only in environment/secret management. GET APIs return configured/not-configured status and masked identifiers, never secret values. Every settings, preference, destination, and routing change creates immutable activity/audit with actor, time, before/after-safe fields, and request ID.

## 8. Observability and testing

Measure queued, sent, delivered where supported, failed, retried, dead-lettered, suppressed, provider latency, rate limits, and oldest-message age by channel and environment. Correlate notification ID, meeting/job ID, request/event ID, and deployment version without logging secret content.

Test account enumeration, token replay/expiry, redirect injection, session revocation, Telegram chat verification/revocation, permission changes before delivery, duplicate messages, provider timeout/429/5xx, signed webhook replay, secret redaction, dead-letter recovery, and separation between Bot 1 and Bot 2.

## 9. Frontend contract

| Concern | Code |
| --- | --- |
| Email/Telegram tests | `frontend/app/repositories/http/settings.ts` |
| Endpoints | `APP_CONFIG_TEST_EMAIL`, `APP_CONFIG_SEND_TEST_EMAIL`, `APP_CONFIG_TEST_TELEGRAM`, `APP_CONFIG_SEND_TEST_TELEGRAM` |
