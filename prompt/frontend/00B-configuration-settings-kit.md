# Prompt 00B — Configuration & Settings Reusable Kit

> **Status:** Implemented — architecture reference only (not a build ticket).
> Key code: `config/configuration-schemas.ts`, `config/settings-schemas.ts` (`storageSettingsTabs`), `repositories/*` (mock now / HTTP when `useMockData=false`), list/editor components under `components/configuration/` and settings pages.
> Developer inventory: `frontend/docs/reusable-components-guide.md`.

## Reference (was copy/paste prompt)

Build and reuse the Docetra **Configuration & Settings** shared kit already started under `frontend/`. Do not invent a second UI kit. Prefer existing Nuxt UI primitives and the components listed below.

### Technology baseline

Follow versions in `prompt/frontend/README.md` and `frontend/package.json`. Mock-only for this phase — no backend APIs, Docker, or migrations.

### Architecture

```text
Pages
  → Feature editors / Settings panels
  → Composables
  → Repository interface
  → Mock repository (localStorage) now / HTTP later
```

Use `useConfigurationRepositories()` and `useSettingsRepositories()` from `app/repositories/index.ts`. Never import mock arrays into page components.

### Types

- `app/types/docetra/configuration.ts` — RecordType, RecordAttribute, options, validation, visibility, workflow
- `app/types/docetra/settings.ts` — AppInfo, AppConfig, Email, Telegram, Storage, ConnectionStatus

### Shared common components (`app/components/common/`)

| Component | Purpose |
| --- | --- |
| `AppConfirmDialog` + `AppConfirmHost` / `useConfirm` | Destructive / save / leave confirms |
| `AppSecretInput` | Masked secret with reveal toggle |
| `AppConnectionStatusCard` | Mock connection status + disclaimer |
| `AppConnectionTestButton` | Trigger simulated test |
| `AppIconPicker` | Lucide icon picker modal |
| `AppColorPicker` | Color input + presets |
| `AppImageUploadField` | Drag-drop image with preview/replace/remove |
| `AppSortableList` | HTML5 drag-and-drop reorder |
| `AppLiveSearch` / `AppFilterSelect` / `AppMultiSelect` | Toolbar search & filters |

Do **not** recreate removed stubs: `AppFormSection`, `AppStatusBadge`, `AppUnsavedChangesDialog`, `AppSettingCard`, `AppSettingsPlaceholder`.

### Configuration builders (`app/components/configuration/`)

| Component | Purpose |
| --- | --- |
| `AppAttributeOptionsBuilder` | Enum options CRUD + reorder |
| `AppValidationRuleBuilder` | Type-aware validation controls |
| `AppVisibilityRuleBuilder` | Field / operator / value rule |
| `AppWorkflowStageBuilder` | Stages + transitions list |
| `AppNumberingPreview` | e.g. `DOC-2026-000001` |
| `AppConfigEntityList` | Shared config index shell |
| `AppRecordTypeList` / `AppRecordAttributeList` | Config indexes |
| `AppRecordTypeEditor` / `AppRecordAttributeEditor` | Config editors via `AppDocumentPage` |

Field rendering uses `AppDynamicFieldRenderer` (no separate Field/Form Preview panels).

### Settings pages

Compose with `AppDocumentPage` + schemas in `settings-schemas.ts`. No dedicated settings card kit.

### Navigation

Sidebar group label must be **Settings** (`docetra.navigation.settings`), routes remain `/settings/*`.

### Rules

1. Reuse these components before creating duplicates.
2. Persist mock data only inside repositories (localStorage keys `docetra:config:*`, `docetra:settings:*`).
3. Label all connection tests as simulated mock behavior.
4. Mask secrets; never log plaintext tokens/passwords.
5. Keep pages thin; put orchestration in composables.
6. Preserve unrelated modules.

### Acceptance

Reusable kit exists, typed repositories work, builders render, Settings nav label is correct, and Configuration / Settings pages compose these pieces without rewriting the foundation.
