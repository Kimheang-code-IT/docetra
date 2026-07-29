# Prompt 06 — Document

## Copy/paste prompt

Implement the general Document page at `/records/documents` using the existing Nuxt 4, TypeScript, and Nuxt UI 4 architecture.

### Implement now

Create only the localized header, Record > Document breadcrumb, route/permission metadata, and standard placeholder. Do not duplicate incoming/outgoing implementations and do not request data.

### Future UI contract

This will be the unified document explorer across permitted document categories. Use server-side pagination, search, sorting, and filters for direction/type, organization, department, status, stage, date, owner, and attachment presence. Support saved/shareable URL filters later. Keep incoming and outgoing distinctions visible without duplicating source-of-truth records. Detail views must show relationships, attachments, current workflow, and history.

### Acceptance

The blank route loads without 404 or API calls and is active under Record.

