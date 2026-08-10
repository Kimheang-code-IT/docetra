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
| General | Locale defaults, feature flags |
| Email | SMTP settings, connection status, last test |
| Telegram | Bot token (masked), webhook, test |
| System | Read-only mode, default page size, env info |
| Display | `cardFields`, `cardFooterAlign` per entity key |

**Display settings** feed board UIs:

- `meetingTopics`, `meetingHistory`
- `incomingDocuments`, `outgoingDocuments`, `documents`, `masterListRequests`

Frontend cache: `useCardFields` + `invalidateCardFieldsCache()` after save.

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
| POST | `/api/v2/settings/app-config/telegram/test-connection` | Bot test |
| POST | `/api/v2/settings/app-config/telegram/send-test` | Send test message |
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
| Read-only mode | System tab flag blocks mutating APIs globally (503 or 403) |

---

## 6. Permissions

| Code | Use |
| --- | --- |
| `settings.app_info.view` / `.edit` | App info |
| `settings.app_config.view` / `.edit` | App config |
| `settings.storage.view` / `.edit` | Storage |

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

---

## 9. Cross-module effects

| Setting | Consumers |
| --- | --- |
| `display.cardFields` | Meeting & record boards (Incoming/Outgoing/Document slots include `documentType`, office, officers, external units) |
| `general.defaultPageSize` | List default limit; UI also offers **All** (`limit=all`, capped server-side) |
| `system.readOnlyMode` | Write API guard |
| Storage default | Portal upload, attachments, Drive sync |

---

*Settings UI uses document-page pattern, not entity workspace tables — backend can still expose one JSON document per aggregate.*
