# Prompt 24 — Record Attribute

## Copy/paste prompt

Implement the Record Attribute page at `/configuration/record-attributes` using the existing Docetra Nuxt UI architecture. Follow the shared foundation and `prompt/specification/modules/admin-config.md`.

### Implement now

Render only the localized Record Attribute title, Configuration breadcrumb, administrative permission metadata, and standard placeholder. Do not create a schema builder, table, field editor, mock rows, or request.

### Future UI contract

The finished page will manage configurable record fields with stable code, localized label, datatype, validation rules, visibility, enabled state, and record-type usage. Large attribute catalogs require server-side pagination/search/filtering. Datatype changes that could invalidate existing values must be blocked or handled through an explicit migration workflow. All changes must be validated by the backend and preserved in audit history.

### Acceptance

The blank route loads through Configuration navigation with correct active state and no data request.

