# Prompt 28 — Settings · Storage

## Copy/paste prompt

Implement `/settings/storage` using the Settings kit. Follow `00B-configuration-settings-kit.md`.

Use `useSettingsRepositories().storage`.

### Provider cards

Show providers: Local Storage, Cloudflare R2, Amazon S3, MinIO, Google Drive.

Each card: name, type, default badge, connection status, bucket/folder, last tested, actions.

### Provider form

Common: configuration name, type, active, set as default, max file size, allowed types, public/private, upload path pattern.

S3-compatible: endpoint, region, bucket, access key, secret (`AppSecretInput`), public URL, path style.

Google Drive: folder ID, credential status, sync status, schedule.

Actions: Test connection (mock + `AppConnectionStatusCard`), Save, Set as default, Disable, View details.

**Only one provider can be default.** Cannot delete the default provider without assigning another first.

### Acceptance

Providers list/edit; mock connection tests; single default enforced; secrets masked; persistence across refresh.
