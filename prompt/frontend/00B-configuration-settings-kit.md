# Prompt 00B — Configuration & Settings Reusable Kit

> **Status:** Implemented — architecture reference only (not a build ticket).
> Key code: `config/configuration-schemas.ts`, `config/settings-schemas.ts` (includes Display / card fields + `storageSettingsTabs`), `repositories/*` (mock when `useMockData`, HTTP otherwise), list/editor components under `components/configuration/` and `components/settings/`.
> Developer inventory: `frontend/docs/reusable-components-guide.md`.

## Reference (was copy/paste prompt)

Build and reuse the Docetra **Configuration & Settings** shared kit already started under `frontend/`. Do not invent a second UI kit. Prefer existing Nuxt UI primitives and the components listed below.

### Technology baseline

Follow versions in `prompt/frontend/README.md` and `frontend/package.json`.

### Architecture

```text
Pages
  → Feature editors / Settings panels
    → Composables
    → Repository interface
    → Mock repository (localStorage) when useMockData
    → HTTP repository when useMockData=false
```

Use `useConfigurationRepositories()` and `useSettingsRepositories()` from `app/repositories/index.ts`. Never import mock arrays into page components.

### Types

- `app/types/docetra/configuration.ts` — RecordType, RecordAttribute, options, validation, visibility, workflow
- `app/types/docetra/settings.ts` — AppInfo, AppConfig (incl. `display.cardFields` / `cardFooterAlign`), Email, Telegram, Storage, ConnectionStatus, font size

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
| `AppLiveSearch` / `AppFilterSelect` / `AppSingleFilterSelect` / `AppMultiSelect` | Toolbar search & filters |
| `AppDateRangeFilter` / `AppInputDate` | Date / range filters |
| `AppRolePermissionMatrix` | Role × document-type permissions |

Shared orchestration helpers:

- `usePathModel` provides nested schema field get/set behavior for Settings and other schema-driven documents.
- `useAppPageTitle` owns the repeated shell-title, locale reaction, cleanup, and SEO lifecycle.
- `utils/role/access.ts` derives action capabilities from an entity's canonical `.view` namespace.

Do **not** recreate removed stubs: `AppFormSection`, `AppStatusBadge`, `AppUnsavedChangesDialog`, `AppSettingCard`, `AppSettingsPlaceholder`.

### Configuration builders (`app/components/configuration/`)

| Component | Purpose |
| --- | --- |
| `AppAttributeOptionsBuilder` | Enum options CRUD + reorder |
| `AppValidationRuleBuilder` | Type-aware validation controls |
| `AppVisibilityRuleBuilder` | Field / operator / value rule |
| `AppWorkflowStageBuilder` | Stages + transitions list |
| `AppConfigEntityList` | Shared config index shell |
| `AppRecordTypeList` / `AppRecordAttributeList` | Config indexes |
| `AppRecordTypeEditor` / `AppRecordAttributeEditor` | Config editors via `AppDocumentPage` |

Field rendering uses `AppDynamicFieldRenderer` (no separate Field/Form Preview panels). Record document pages also consume record-type attributes via `useRecordTypeDrivenTabs`.

`prompt/frontend/00C-dynamic-record-fields.md` is the authoritative extension for dynamic fields. Treat `/configuration/record-attributes` as the global **Attribute Catalog**, and extend `AppRecordTypeEditor` with versioned Fields & layout composition. The current four-entity `useRecordTypeDrivenTabs` behavior is transitional; all record-backed entities, including Meeting and Meeting Topic, must consume the same resolved published schema.

Each Record Type table row includes **Assign fields**, which deep-links to its assignment editor. Assigned-field rows and workflow-stage rows are drag-sortable; each field row may optionally reference a configured stage. Incoming, Outgoing, Document, and Master List Request boards resolve this saved stage list and order at runtime.

### Settings pages

Compose with `AppDocumentPage` + schemas in `settings-schemas.ts`. No dedicated settings card kit.

| Route | Notes |
| --- | --- |
| `/settings/app-info` | Branding / product info |
| `/settings/app-config` | General, email, telegram, system, **display (card fields)** |
| `/settings/storage` | Storage backends via `storageSettingsTabs` |

Settings routes require `.view`; editing requires `.edit`; reset, connection tests, activation, and set-default controls require `.configure`. Apply `readOnly` and `canSave` through `AppDocumentPage` instead of duplicating disabled-state logic in every page.

### Settings display / card fields (`app/components/settings/`)

| Component / API | Purpose |
| --- | --- |
| `AppCardFieldsEditor` | Per-entity slot checklist + footer align (field type `card-fields-editor`) |
| `AppCardFieldPreview` | Live card preview while editing |
| `useCardFields` / `invalidateCardFieldsCache` | Boards read visibility from App Config |
| `utils/card-fields.ts` | Slot catalogs for meeting + record entities |

Entities covered: `meetingTopics`, `meetingHistory`, `incomingDocuments`, `outgoingDocuments`, `documents`, `masterListRequests`.

### Navigation

Sidebar group label must be **Settings** (`docetra.navigation.settings`), routes remain `/settings/*`. Font size lives in the **user menu**, not a settings route.

### Rules

1. Reuse these components before creating duplicates.
2. Persist mock data only inside repositories (localStorage keys `docetra:config:*`, `docetra:settings:*`).
3. Label all connection tests as simulated mock behavior when mock mode is on.
4. Mask secrets; never log plaintext tokens/passwords.
5. Keep pages thin; put orchestration in composables.
6. Preserve unrelated modules.
7. After saving App Config display settings, invalidate card-fields cache so boards update.
8. After publishing a record type or attribute change, invalidate the resolved record-schema cache.
9. Do not hard-delete published/used attributes or silently mutate stable attribute/option codes.
10. Use the shared safe raster image rules for branding uploads; do not allow SVG/active content in inline previews.
11. Frontend permission visibility is advisory. The Settings and Configuration APIs must enforce the same action key.

### Acceptance

Reusable kit exists, typed repositories work (mock + HTTP switch), builders render, Settings nav label is correct, card-fields editor drives board cards, and Configuration / Settings pages compose these pieces without rewriting the foundation.
