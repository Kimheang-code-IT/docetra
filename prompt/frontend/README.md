# Docetra Frontend Page Prompts

This folder contains implementation prompts for building the Docetra v2 frontend in the existing `frontend/` Nuxt application.

## Current objective

Build the complete Docetra operational UI from a reusable workspace system:

- Server-backed tables for large datasets.
- Stage-based Kanban boards for workflow records.
- Responsive ERP-style create, detail, and edit document pages built with Nuxt UI.
- Reusable comments and activity timelines matching the supplied reference.
- Shared search, filters, date range, sorting, pagination, attachments, and permissions.
- Configuration-driven fields for record types and attributes.

## Technology baseline

Use the technology already installed in `frontend/`:

- Nuxt 4 and Vue 3
- TypeScript with `<script setup lang="ts">`
- Nuxt UI 4
- Tailwind CSS 4
- Pinia
- Nuxt i18n
- VueUse
- TanStack Vue Table for future large datasets
- ECharts for future dashboard visualizations

## How to use these prompts

1. Read [`00-product-ui-design-map.md`](./00-product-ui-design-map.md).
2. Implement [`00-reusable-workspace-components.md`](./00-reusable-workspace-components.md).
3. Apply [`00-shared-foundation.md`](./00-shared-foundation.md).
4. Run the page prompts in numeric order, or select one module at a time.
5. Reuse shared components; page files should primarily configure fields, filters, actions, and views.

## Route inventory

| # | Sidebar group | Page | Route | Prompt |
|---|---|---|---|---|
| 1 | — | Dashboard | `/` | `01-dashboard.md` |
| 2 | Meeting | Topic | `/meetings/topics` | `02-meeting-topic.md` |
| 3 | Meeting | History | `/meetings/history` | `03-meeting-history.md` |
| 4 | Record | Incoming Document | `/records/incoming-documents` | `04-record-incoming-document.md` |
| 5 | Record | Outgoing Document | `/records/outgoing-documents` | `05-record-outgoing-document.md` |
| 6 | Record | Document | `/records/documents` | `06-record-document.md` |
| 7 | Record | Master List Request | `/records/master-list-requests` | `07-record-master-list-request.md` |
| 8 | Record | Log | `/records/logs` | `08-record-log.md` |
| 9 | Organization | Department | `/organizations/departments` | `09-organization-department.md` |
| 10 | Organization | Company | `/organizations/companies` | `10-organization-company.md` |
| 11 | Organization | Company Purpose | `/organizations/company-purposes` | `11-organization-company-purpose.md` |
| 12 | Organization | Company Sector | `/organizations/company-sectors` | `12-organization-company-sector.md` |
| 13 | Organization | Officer | `/organizations/officers` | `13-organization-officer.md` |
| 14 | User Management | Role | `/user-management/roles` | `14-user-management-role.md` |
| 15 | User Management | User | `/user-management/users` | `15-user-management-user.md` |
| 16 | Portal | File Upload | `/portal/file-upload` | `16-portal-file-upload.md` |
| 17 | Portal | Google Drive Sync | `/portal/google-drive-sync` | `17-portal-google-drive-sync.md` |
| 18 | Portal | Log | `/portal/logs` | `18-portal-log.md` |
| 19 | System Monitor | System Log | `/system-monitor/system-logs` | `19-system-monitor-system-log.md` |
| 20 | Auth | Login | `/login` | `20-auth-login.md` |
| 21 | Auth | Forget Password | `/forget-password` | `21-auth-forget-password.md` |
| 22 | Auth | OTP Verification | `/otp` | `22-auth-otp.md` |
| 23 | Configuration | Record Type | `/configuration/record-types` | `23-configuration-record-type.md` |
| 24 | Configuration | Record Attribute | `/configuration/record-attributes` | `24-configuration-record-attribute.md` |
| 25 | Configuration | Document Type | `/configuration/document-types` | `25-configuration-document-type.md` |

## Product references

Before implementing the later full UI, consult:

- `prompt/specification/00-overview.md`
- `prompt/specification/03-functional-requirements.md`
- `prompt/specification/04-permissions-and-access.md`
- `prompt/specification/05-user-flows.md`
- `prompt/specification/06-api-contracts.md`
- `prompt/specification/08-shared-standards.md`
- The relevant file under `prompt/specification/modules/`
