# Prompt 24 — Record Attribute

## Copy/paste prompt

Implement `/configuration/record-attributes` as schema-field management. Follow `00-shared-foundation.md` and `00B-configuration-settings-kit.md`.

Use `useConfigurationRepositories().attributes`. Build this module **before** Record Type.

### List view

Columns: Label, Field code, Data type, Used by count, Required default, Searchable, Status, Updated, Actions.

Filters: search, data type, status. Pagination. Actions: Create, Edit, Duplicate, Preview, Activate/Deactivate, Delete (confirm).

Routes: `/configuration/record-attributes`, `/new`, `/:id`.

### Editor sections

1. **Basic Information** — label, code, description, help text, data type, placeholder, active  
   Supported types: Short/Long/Rich Text, Integer, Decimal, Currency, Boolean, Date, Time, DateTime, Email, Phone, URL, Select, Multi Select, Radio, Checkbox Group, File, Image, Organization, Officer, User, Record Reference. Rich Text uses TipTap (`AppRichTextNote` / `UEditor`) on live forms.
2. **Field Configuration** — default, required, unique, read-only, searchable, filterable, sortable, show in list
3. **Validation** — `AppValidationRuleBuilder` (type-aware)
4. **Options** — only for select-like types via `AppAttributeOptionsBuilder` (no separate Enum page)
5. **Visibility** — `AppVisibilityRuleBuilder`
6. **Preview** — `AppDynamicFieldPreview`

Guard risky datatype changes when the attribute is already used. Prefer disable over delete when referenced.

### Acceptance

All supported types can be configured; options/validation/visibility work; preview updates live; repository swap to HTTP later does not rewrite pages.
