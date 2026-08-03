# Docetra Frontend Page Prompts

This folder contains implementation prompts for building the Docetra v2 frontend in the existing `frontend/` Nuxt application.

## Current objective

Build the complete Docetra operational UI from a reusable workspace system:

- Server-backed tables for large datasets with per-row action menus.
- Stage-based Kanban boards for workflow records.
- Split boards (1+3) for Meeting Topics, Record Logs, and File Upload (Uppy left).
- Responsive ERP-style create, detail, and edit document pages built with Nuxt UI.
- Meeting notes via TipTap (`UEditor`) + Uppy large uploads.
- Reusable comments and activity timelines.
- Shared search, filters, date range, sorting, pagination, attachments, and permissions.
- Configuration-driven fields for record types and attributes.

## Technology baseline

Use the technology already installed in `frontend/package.json` (do not invent newer majors). Keep versions aligned with that file when bumping deps.

| Package | Version |
| --- | --- |
| `nuxt` | `^4.3.1` |
| `vue` | `^3.5.29` |
| `typescript` | `^5.9.3` |
| `vue-tsc` | `^3.2.5` |
| `@nuxt/ui` | `^4.5.1` (includes `UEditor`) |
| `tailwindcss` | `^4.2.1` |
| `pinia` / `@pinia/nuxt` | `^3.0.4` / `^0.11.3` |
| `@nuxtjs/i18n` | `^10.2.3` (default locale: English) |
| `@vueuse/core` / `@vueuse/nuxt` | `^14.2.1` |
| `@tanstack/vue-table` | `^8.21.3` |
| TipTap (`@tiptap/*`) | `3.29.2` exact — pin all via `pnpm.overrides`; single `@tiptap/pm` |
| `@uppy/core` / `@uppy/dashboard` / `@uppy/xhr-upload` | `^5.2.0` / `^5.1.1` / `^5.2.0` |
| `@uppy/vue` | `^3.2.0` |
| `echarts` / `vue-echarts` | `^6.0.0` / `^8.0.1` |
| `zod` | `^4.3.6` |
| `@nuxt/image` | `^2.0.0` |
| `@internationalized/date` | `^3.12.0` |
| `@nuxt/fonts` | `^0.14.0` |
| Package manager | `pnpm@10.30.3` |

Use `<script setup lang="ts">`. Do not add a second UI kit, state library, chart library, or duplicate TipTap/ProseMirror tree.

### App version

- Public version: `runtimeConfig.public.appVersion` from `NUXT_PUBLIC_APP_VERSION` (default `0.1.0` in `nuxt.config.ts`).
- Display only in the About dialog version badge (`AppAboutDialog`). Bump via env or the nuxt.config default — do not hardcode a second version string in UI.

### Shell padding

| Surface | Padding |
| --- | --- |
| List / main (workspace, dashboard, settings, portal) | `px-1.5 pt-1.5 pb-0` |
| Document detail / create | `p-0` (edge-to-edge under header) |
| Header navbar | `px-1.5` horizontal |

### Loading

- No custom `App*Skeleton` components.
- Prefer Nuxt UI defaults: `UTable` `:loading`, light spinner overlays elsewhere; keep virtualized rows while refreshing.

### Navigation notes

- Sidebar: Dashboard, Meeting, Record, Organization, User Management, Portal, Configuration, Settings.
- **System Log** is not a sidebar group — open it from the **user menu** (`useUserMenu`) → System Log → `/system-monitor/system-logs`.
- Record / Portal list titles use plural **Logs** (`docetra.pages.recordLog`, `docetra.pages.portalLog`).

## How to use these prompts

1. Read [`00-product-ui-design-map.md`](./00-product-ui-design-map.md).
2. Implement [`00-reusable-workspace-components.md`](./00-reusable-workspace-components.md).
3. Apply [`00-shared-foundation.md`](./00-shared-foundation.md).
4. For Configuration & Settings, implement [`00B-configuration-settings-kit.md`](./00B-configuration-settings-kit.md) first, then prompts 23–28 (Record Attribute before Record Type).
5. Run other page prompts in numeric order, or select one module at a time.
6. Reuse shared components; page files should primarily configure fields, filters, actions, and views.

## Route inventory

| # | Nav location | Page | Route | Prompt |
|---|---|---|---|---|
| 1 | Sidebar — | Dashboard | `/` | `01-dashboard.md` |
| 2 | Sidebar · Meeting | Topic | `/meetings/topics` | `02-meeting-topic.md` |
| 3 | Sidebar · Meeting | History | `/meetings/history` | `03-meeting-history.md` |
| 4 | Sidebar · Record | Incoming Document | `/records/incoming-documents` | `04-record-incoming-document.md` |
| 5 | Sidebar · Record | Outgoing Document | `/records/outgoing-documents` | `05-record-outgoing-document.md` |
| 6 | Sidebar · Record | Document | `/records/documents` | `06-record-document.md` |
| 7 | Sidebar · Record | Master List Request | `/records/master-list-requests` | `07-record-master-list-request.md` |
| 8 | Sidebar · Record | Logs | `/records/logs` | `08-record-log.md` |
| 9 | Sidebar · Organization | Department | `/organizations/departments` | `09-organization-department.md` |
| 10 | Sidebar · Organization | Company | `/organizations/companies` | `10-organization-company.md` |
| 11 | Sidebar · Organization | Company Purpose | `/organizations/company-purposes` | `11-organization-company-purpose.md` |
| 12 | Sidebar · Organization | Company Sector | `/organizations/company-sectors` | `12-organization-company-sector.md` |
| 13 | Sidebar · Organization | Officer | `/organizations/officers` | `13-organization-officer.md` |
| 14 | Sidebar · User Management | Role | `/user-management/roles` | `14-user-management-role.md` |
| 15 | Sidebar · User Management | User | `/user-management/users` | `15-user-management-user.md` |
| 16 | Sidebar · Portal | File Upload | `/portal/file-upload` | `16-portal-file-upload.md` |
| 17 | Sidebar · Portal | Google Drive Sync | `/portal/google-drive-sync` | `17-portal-google-drive-sync.md` |
| 18 | Sidebar · Portal | Logs | `/portal/logs` | `18-portal-log.md` |
| 19 | User menu | System Log | `/system-monitor/system-logs` | `19-system-monitor-system-log.md` |
| 20 | Auth | Login | `/auth/login` | `20-auth-login.md` |
| 21 | Auth | Forget Password | `/auth/forget-password` → verify → reset | `21-auth-forget-password.md` |
| 22 | Auth | Verify code / Reset password | `/auth/verify-code`, `/auth/reset-password` | `22-auth-otp.md` |
| 23 | Sidebar · Configuration | Record Type | `/configuration/record-types` | `23-configuration-record-type.md` |
| 24 | Sidebar · Configuration | Record Attribute | `/configuration/record-attributes` | `24-configuration-record-attribute.md` |
| 25 | Sidebar · Configuration | Document Type | `/configuration/document-types` | `25-configuration-document-type.md` |
| 26 | Sidebar · Settings | App Info | `/settings/app-info` | `26-settings-app-info.md` |
| 27 | Sidebar · Settings | App Config | `/settings/app-config` | `27-settings-app-config.md` |
| 28 | Sidebar · Settings | Storage | `/settings/storage` | `28-settings-storage.md` |

## Product references

Before implementing the later full UI, consult:

- `prompt/specification/00-overview.md`
- `prompt/specification/03-functional-requirements.md`
- `prompt/specification/04-permissions-and-access.md`
- `prompt/specification/05-user-flows.md`
- `prompt/specification/06-api-contracts.md`
- `prompt/specification/08-shared-standards.md`
- The relevant file under `prompt/specification/modules/`
- Configuration & Settings kit: [`00B-configuration-settings-kit.md`](./00B-configuration-settings-kit.md)
