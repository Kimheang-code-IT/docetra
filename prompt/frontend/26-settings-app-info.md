# Prompt 26 — Settings · App Info

## Copy/paste prompt

Implement `/settings/app-info` using the Settings reusable kit (`00B-configuration-settings-kit.md`). Replace `AppSettingsPlaceholder`.

Use `useSettingsRepositories().appInfo`. Persist via mock repository / localStorage.

### Layout

Three `AppSettingCard` sections + sticky Save / Reset / Preview. Warn with `AppUnsavedChangesDialog` when leaving dirty.

#### General Information

Application name, short name, organization name, description, support email/phone, website, address.

#### Branding

Main logo, sidebar logo, favicon, login background via `AppImageUploadField`; primary/secondary colors via `AppColorPicker`. Live branding preview panel. On save in mock mode, apply visible name/logo/colors through `usePreferencesStore` / runtime brand helpers where practical.

#### Footer Information

Copyright text, privacy-policy URL, terms URL.

### Acceptance

Admins can edit identity and branding, preview changes, save/reset, and retain values after refresh.
