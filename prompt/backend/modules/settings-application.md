# Settings — App Info, App Config & Storage (Backend Logic)

> **UI scope:** Settings nav — **App Info**, **App Config**, **Storage**.  
> **References:** `prompt/specification/modules/admin-config.md` (settings), `prompt/specification/modules/storage-integration.md`, `frontend/app/config/settings-schemas.ts`, `repositories/contracts/settings.ts`.

---

## 1. Purpose

Settings are **singleton or small-set** configuration surfaces (not high-volume CRUD):

| Route | UI | Data |
| --- | --- | --- |
| `/settings/app-info` | `AppDocumentPage` | Branding, legal, login background |
| `/settings/app-config` | `AppDocumentPage` | General, email, telegram, system, **display/card fields** |
| `/settings/storage` | Storage providers panel | Providers, default, connection test |

Changes affect **runtime behavior** (email, pagination default, card layouts, upload targets).

---

## 2. Domain aggregates

### App info (`AppInfo`)

| Section | Examples |
| --- | --- |
| Brand | App name, logo URL, tagline |
| Legal | Copyright, support email |
| Auth UI | Login background URL |

Single document GET/PUT; optional reset to defaults.

### App config (`AppConfig`)

| Tab | Backend sections |
| --- | --- |
| General | Language, locale, timezone, formatting defaults, feature flags |
| Email | SMTP settings, connection status, last test |
| Telegram | Separate Meeting Bot and Development Bot configured/masked status, allowlists, event policy, connection tests |
| System | Read-only mode, default page size, env info |
| Display | `cardFields`, `cardFooterAlign` per entity key |
| Google (future) | Independently enabled Sign-In, Calendar, Drive, and Gmail capability status; approved domains/resources; safe connection health |

**Display settings** feed board UIs:

- `meetingTopics`, `meetingHistory`
- `incomingDocuments`, `outgoingDocuments`, `documents`, `masterListRequests`

Frontend cache: `useCardFields` + `invalidateCardFieldsCache()` after save.

**Localization fields are an app-wide contract:** `defaultLanguage`, `availableLanguages`, `locale`, IANA `timezone`, `dateFormat`, `timeFormat`, `firstDayOfWeek`, `numberFormat`, and `currency`. The backend validates supported locale/timezone identifiers and returns UTC ISO 8601 timestamps; the frontend formats them at the display boundary. Pages must not hard-code these values.

**Meeting scheduler settings:** `meetingReminderOffsetsMinutes`, `meetingRecurrenceHorizonDays`, and the imminent-display threshold are validated App Config values consumed by the APScheduler service. Scheduler engine/timezone/misfire/concurrency settings remain deployment configuration and are not editable from ordinary application settings.

### Storage providers

| Field | Role |
| --- | --- |
| `id`, `name`, `type` | local, s3, google_drive, … |
| `active`, `isDefault` | Routing uploads |
| `accessMode`, `maxFileSizeMb`, `allowedFileTypes` | Policy |
| Secrets | Encrypted; masked in API |

---

## 3. Flows

### Edit app info

1. Load `GET /api/v2/settings/app-info`.
2. User updates branding fields + image upload (URL or storage upload).
3. `PUT` full or partial document.
4. About dialog reads `runtimeConfig.public.appVersion` + app info name/logo.

### Edit app config

1. Load `GET /api/v2/settings/app-config`.
2. Tabbed save per section or whole document.
3. **Test connection** endpoints (email/telegram) — side effect only, no full save required.
4. On display tab save → boards refresh card layout (client invalidates cache).

### Configure notification routing

1. An administrator configures Meeting Bot and Development Bot independently; secret values are write-only.
2. The backend verifies a Telegram group and adds it to the correct bot's destination allowlist.
3. The administrator maps meeting events to user groups and technical/version events to private IT groups.
4. A meeting editor may choose only approved destinations within their organization/department scope.
5. Each user may customize permitted channels, reminder offsets, quiet hours, timezone, and language without changing organization-wide routing.
6. Saving invalidates the notification-config cache and writes immutable activity; workers consume the new version without restart.

Google Workspace is configured as a separate future integration surface. App Config stores only non-secret policy and masked connection status; OAuth credentials and tokens remain encrypted on the backend. Follow `../05-google-workspace-integration.md` for connect/revoke, Calendar, Drive, Gmail, scope, queue, and audit behavior.

### Storage provider lifecycle

```text
List providers → create/edit → test-connection → set-active / set-default
Upload modules resolve default provider id on each upload
```

---

## 4. API surface (aligned with frontend)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v2/settings/app-info` | Read app info |
| PUT/PATCH | `/api/v2/settings/app-info` | Update |
| POST | `/api/v2/settings/app-info/reset` | Factory reset |
| GET | `/api/v2/settings/app-config` | Read app config |
| PUT/PATCH | `/api/v2/settings/app-config` | Update |
| POST | `/api/v2/settings/app-config/email/test-connection` | SMTP test |
| POST | `/api/v2/settings/app-config/email/send-test` | Send test mail |
| POST | `/api/v2/settings/app-config/telegram/meeting/test-connection` | Meeting Bot connectivity/identity test |
| POST | `/api/v2/settings/app-config/telegram/meeting/send-test` | Send to an allowlisted Meeting Bot test chat |
| POST | `/api/v2/settings/app-config/telegram/devops/test-connection` | Development Bot connectivity/identity test |
| POST | `/api/v2/settings/app-config/telegram/devops/send-test` | Send to an allowlisted private development chat |
| GET/POST/PATCH | `/api/v2/settings/app-config/telegram/{meeting|devops}/destinations[/{id}]` | Manage verified group allowlists and routing policy |
| GET/PATCH | `/api/v2/users/me/notification-preferences` | Read/update the signed-in user's allowed notification preferences |
| GET | `/api/v2/settings/storage` | List providers |
| GET/PATCH | `/api/v2/settings/storage/{id}` | Detail/update |
| POST | `/api/v2/settings/storage/{id}/test-connection` | Provider test |
| POST | `/api/v2/settings/storage/{id}/set-default` | Default provider |
| POST | `/api/v2/settings/storage/{id}/set-active` | Enable/disable |

---

## 5. Security

| Rule | Detail |
| --- | --- |
| Secrets | Write-only fields; GET returns `***` or omit |
| Permissions | Separate view vs edit for settings |
| Test endpoints | Rate limited; no arbitrary recipient without permission |
| Bot isolation | Meeting and Development bots use separate secrets, allowlists, routes, and audit events |
| Configure actions | Reset, connection tests, set-default, and provider activation require `.configure` |
| Images | Detect and allow safe raster content; do not trust file extension or browser MIME; reject active SVG for inline branding previews |
| Read-only mode | System tab flag blocks mutating APIs globally (503 or 403) |

---

## 6. Permissions

| Code | Use |
| --- | --- |
| `settings.app_info.view` / `.edit` / `.configure` | Read/update/reset app info |
| `settings.app_config.view` / `.edit` / `.configure` | Read/update/test app config connections |
| `users.notification_preferences.view` / `.edit` | Read/update personal channels, reminders, quiet hours, timezone, and language |
| `settings.storage.view` / `.edit` / `.configure` | Read/update/test/default storage providers |

---

## 7. Frontend contract

| Concern | Code |
| --- | --- |
| Schemas | `config/settings-schemas.ts` (`storageSettingsTabs`, app config tabs) |
| Types | `types/docetra/settings.ts` |
| Repositories | `useSettingsRepositories()` |
| Card editor | `AppCardFieldsEditor`, `AppCardFieldPreview` |
| Pages | `pages/settings/app-info`, `app-config`, `storage` |
| Endpoints | `api-endpoints.ts` (APP_INFO*, APP_CONFIG*, STORAGE_*) |

**Mock keys:** `docetra:settings:app-info`, `docetra:settings:app-config`, `docetra:settings:storage`.

**App version display:** `NUXT_PUBLIC_APP_VERSION` / `runtimeConfig.public.appVersion` — not stored in app config unless product adds explicit override field.

---

## 8. Validation

| Case | Result |
| --- | --- |
| Invalid email/Telegram config | Test endpoint fails with message |
| Only one default provider | Enforced on set-default |
| Deactivate default provider | 422 unless new default set |
| Invalid card field slot name | 422 against allowed catalog |
| Invalid locale, format, or IANA timezone | 422 with field error |

---

## 9. Cross-module effects

| Setting | Consumers |
| --- | --- |
| `display.cardFields` | Meeting & record boards (Incoming/Outgoing/Document slots include `documentType`, office, officers, external units) |
| `general.defaultPageSize` | List default limit; UI also offers **All** (`limit=all`, capped server-side) |
| General localization fields | Every date, time, number, currency, translated label, and calendar control |
| `system.readOnlyMode` | Write API guard |
| Storage default | Portal upload, attachments, Drive sync |

---

*Settings UI uses document-page pattern, not entity workspace tables — backend can still expose one JSON document per aggregate.*
