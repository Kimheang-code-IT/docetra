# Prompt 07 — Master List Request

## Copy/paste prompt

Implement `/records/master-list-requests` as a scaffold page in the existing Docetra Nuxt UI frontend.

### Implement now

Add the localized Master List Request title, Record breadcrumb, permission metadata, and shared placeholder card only. Do not invent workflow fields or backend endpoints.

### Future UI contract

The later UI will track master-list requests as configured record types with requester, owning organization/department, request date, status, stage, waiting state, assignee, related records, attachments, and history. Fields that vary by record type must come from typed configuration/schema metadata rather than hardcoded per-page assumptions. Large results require server-side list operations.

### Acceptance

Navigation and route rendering work, while business UI and network activity remain absent.

