# Prompt 27 — Settings · App Config

## Copy/paste prompt

Implement `/settings/app-config` with lazy-loaded tabs. Follow `00B-configuration-settings-kit.md`.

Use `useSettingsRepositories().appConfig`.

### Tabs

General · Localization · Email · Telegram · Notifications · Security · System

#### General

Default landing page, page size, record view, comments/sharing/export toggles, max upload size.

#### Localization

Default/available languages, timezone, date/time formats, first day of week, number format, currency, locale — searchable selectors.

#### Email

Enable SMTP fields; mask password with `AppSecretInput`; `AppConnectionStatusCard` + `AppConnectionTestButton` for **simulated** test connection / test email. States: Testing, Connected, Failed, Not tested.

#### Telegram

Bot settings; mask token; connection status card; destinations table (name, type, chat ID, org, record type, events, status); message template textarea with variables (`{{record_number}}`, …) — not TipTap. Actions: test connection, send test message, change/disable bot — all mock-simulated.

#### Notifications

In-app / email / telegram toggles, retries, quiet hours, language, event rules.

#### Security

Session timeout, login attempts, lock duration, password expiry, require change, upload extensions, audit retention. Show clear disclaimer: **frontend configuration only — not enforced without backend**.

#### System

Maintenance / read-only (confirm with `AppConfirmDialog`), pagination default, config version, environment, mock cache/job status.

### Acceptance

All tabs load; email/Telegram mock tests work and are labeled simulated; unsaved warning works; data persists via repository.
