# Prompt 23 — Record Type

## Copy/paste prompt

Implement the Record Type page at `/configuration/record-types` in the existing Nuxt 4 and Nuxt UI 4 application. Follow `prompt/frontend/00-shared-foundation.md`, the administrative configuration specification, and the permission rules.

### Implement now

Create only the localized Record Type header, Configuration breadcrumb, administrative route/permission metadata, and shared placeholder card. Do not build a table, form, API integration, or mock configuration data.

### Future UI contract

The completed page will manage stable record-type codes, localized labels, descriptions, enabled state, workflow capability, ordering, and associated template summary. Use server-side pagination, search, filtering, and sorting. Codes must remain stable after adoption, disabling is preferred to destructive deletion, and every configuration change must be permission-protected and auditable.

### Acceptance

The route is reachable from Configuration > Record Type, highlights correctly, makes no API request, and passes the production build.

