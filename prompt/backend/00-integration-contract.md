# Frontend–Backend Integration Contract

This is the implementation contract between the Nuxt frontend and the future Docetra API. It consolidates the behavior already implemented in `frontend/` so backend work can begin without changing page code.

## 1. Runtime topology

### Local development

```text
Browser → Nuxt dev server on host (:3000) → Docker API (:8000)
                                            ├─ PostgreSQL
                                            ├─ Redis (state + short/long cache tiers)
                                            ├─ RabbitMQ → backend worker(s)
                                            ├─ APScheduler → RabbitMQ meeting events
                                            ├─ MinIO/S3-compatible storage
                                            └─ Third parties: Email + Telegram Bots 1/2
```

- Run the frontend directly on the developer computer for fast HMR.
- Run every backend dependency through `compose.backend.yml`.
- Copy `backend.env.example` to a private environment file; never commit real secrets.
- The API must explicitly allow the configured frontend origin. Credentialed CORS must never use `*`.

Production may host or containerize the built frontend, but browser/API traffic must be TLS-only and pass through a trusted reverse proxy.

Redis accelerates safe reads through short and long TTL tiers; PostgreSQL remains authoritative. RabbitMQ handles durable asynchronous jobs and cross-instance events. Follow [`01-cache-and-messaging.md`](./01-cache-and-messaging.md); an API handler must not wait synchronously for file scanning, Drive sync, export generation, notification delivery, or search indexing.

APScheduler is required for meeting reminders, recurrence, and scheduled start/end events. It uses a persistent store, UTC scheduler time, stable IDs, misfire/coalescing rules, and publishes due work to RabbitMQ as defined in [`02-meeting-scheduler.md`](./02-meeting-scheduler.md).

Telegram Bot 1 delivers permission-checked meeting alerts, third-party email delivers forgot-password links, and Telegram Bot 2 delivers private version/code/docs/CI/monitoring events. They are isolated as defined in [`03-notifications-and-integrations.md`](./03-notifications-and-integrations.md).

Optional Google Workspace support is isolated behind backend provider adapters as defined in [`05-google-workspace-integration.md`](./05-google-workspace-integration.md). Google Sign-In, Calendar, Drive, and Gmail are independently enabled; Docetra remains authoritative for permissions, meeting lifecycle, workflow, activity, and APScheduler reminders.

## 2. Authentication, session, and CSRF

- `POST /api/v2/auth/login` validates credentials, issues a signed JWT, sets it on a `Secure`, `HttpOnly`, `SameSite` cookie (`docetra_session`), sets a refresh JWT on `docetra_refresh`, sets a readable CSRF cookie, and returns the safe user profile. It does not return the JWT in JSON.
- JWT claims are `sub`, `jti`, `iat`, `exp`, `typ`. Permissions are not embedded; `/auth/me` reloads them from PostgreSQL. Redis `jwt:{jti}` binds CSRF and enables instant revoke.
- `GET /api/v2/auth/me` is the authoritative session and capability probe.
- `POST /api/v2/auth/refresh` rotates `jti` using the refresh cookie and re-sets cookies. The frontend calls this when `/auth/me` fails with `token_expired`.
- `POST /api/v2/auth/logout` revokes Redis `jti` keys and clears authentication cookies. Password change and reset also revoke outstanding JWTs.
- Cookie-authenticated mutations require same-origin validation plus a CSRF token. The frontend reads `XSRF-TOKEN` and sends `X-CSRF-Token`.
- The frontend sends `credentials: include`. Do not require bearer tokens in local storage or a JavaScript-readable auth cookie.
- `401` means missing/expired session. The frontend opens the shared session dialog, then redirects to login.
- `403` means authenticated but forbidden. The frontend opens the shared permission dialog and remains on the current page; there is no separate forbidden page.
- Route visibility and disabled buttons are usability controls only. The backend enforces every page, resource, field, action, export, upload, comment, assignment, and transition permission.

The frontend's cached user snapshot is not proof of authentication. It is replaced after `/auth/me`, cleared on logout/401, and synchronized across browser tabs.

## 3. Standard envelopes

Successful detail response:

```json
{ "data": { "id": "01...", "version": 3 } }
```

Successful list response:

```json
{
  "data": [{ "id": "01..." }],
  "meta": { "page": 1, "limit": 20, "total": 1, "totalPages": 1 }
}
```

Error response:

```json
{
  "error": {
    "code": "permission_denied",
    "message": "You do not have permission to delete this topic.",
    "fields": {},
    "requestId": "req_..."
  }
}
```

Use `400` for malformed requests, `401` for session failure, `403` for authorization, `404` for an inaccessible/missing resource, `409` for version or uniqueness conflicts, `422` for field validation, `429` for throttling, and `5xx` for server failures. Never expose stack traces or secrets.

All list endpoints are bounded and accept consistent `page`, `limit`, `q`, `sort`, and documented filters. Mutations accept an optimistic `version`/ETag and an idempotency key where retries could duplicate work.

## 4. Canonical lifecycle status

Business records and configuration/master-data cards use exactly:


| API value  | UI label | Meaning                                             |
| ---------- | -------- | --------------------------------------------------- |
| `active`   | Active   | Available for normal use                            |
| `archived` | Archived | Retained but hidden from normal active views        |
| `deleted`  | Deleted  | Soft-deleted tombstone; restore/purge is privileged |


There is no `completed` business lifecycle status. Workflow position is a separate `stageId`; a final stage uses stage metadata such as `isFinal`. Meeting history is determined by archival or meeting time, not a fourth lifecycle value.

Domain state machines remain separate: user accounts may be `active`, `disabled`, or `locked`; jobs/uploads may be pending/running/ready/failed; metadata publication may be draft/published. These values must not populate a business-card Status select.

## 5. Assignment and mention contract

All assignee fields are arrays, even when they contain one item. A reference has a stable ID, display label, and kind:

```json
{
  "assignees": [
    { "id": "officer_5", "label": "Officer 5", "type": "officer" },
    { "id": "department_1", "label": "Department 1", "type": "department" }
  ]
}
```

Allowed types are `officer`, `department`, and `company`. The API stores IDs and type, resolves authoritative labels, de-duplicates by `(type,id)`, preserves user order, removes inaccessible choices, and validates tenant scope.

Mention/assignment option endpoints accept indexed text search (`q`), optional `type`, and a bounded `limit`. Responses must be permission-filtered. The frontend renders one or many removable tags and uses UI colors only as presentation: officer green, department blue, company amber.

## 6. Configuration and localization

`GET/PATCH /api/v2/settings/app-config` owns app-wide defaults; pages must not hard-code them:

- `defaultLanguage`, `availableLanguages`, `locale`
- `timezone`
- `dateFormat`, `timeFormat`, `firstDayOfWeek`
- `numberFormat`, `currency`
- default page size and configurable card fields

Store timestamps in UTC and return ISO 8601. Format dates, times, numbers, and currency at the frontend boundary with the resolved app/user locale and timezone. Validate locale and IANA timezone identifiers server-side.

List and export filters use `startDate` / `endDate`. Picker values may be `YYYY-MM-DD` or `YYYY-MM-DDTHH:mm` without offset; interpret datetime-local strings in the App Config timezone. Full rules: [`07-datetime-and-list-query.md`](./07-datetime-and-list-query.md).

## 7. Required endpoint families

Canonical paths are `frontend/app/utils/constants/api-endpoints.ts`. Do not shorten them. Folder mapping: [`06-backend-file-structure.md`](./06-backend-file-structure.md).

| Area | Prefix / key routes |
| --- | --- |
| Auth | `/auth/login`, `/auth/me`, `/auth/refresh`, `/auth/logout`, `/auth/forgot-password` (+ verify/resend/reset), `/auth/change-password`, `/auth/profile/avatar` |
| Dashboard | `/dashboard/summary` |
| Meetings | `/meetings/topics`, `/meetings/history`, `/meetings/reorder`, `/meetings/history/{id}/assign-topic`, `/meetings/history/{id}/attachments`, `/meetings/history/{id}/attachments/link` |
| Records | `/records/incoming-documents`, `/outgoing-documents`, `/documents`, `/master-list-requests`, `/records/logs` |
| Organization | `/organizations/departments`, `/companies`, `/company-purposes`, `/company-sectors`, `/officers` |
| Access | `/users/roles`, `/users`, `/users/permission-catalog` |
| Configuration | `/configuration/record-types`, `/record-attributes` |
| Settings | `/settings/app-info`, `/app-config`, `/storage` (+ test/set-default/set-active) |
| Portal | `/portal/file-uploads`, `/portal/google-drive-sync`, `/portal/drive-files`, `/portal/logs` |
| System | `/system/logs` |
| Shared | `{base}/{id}/comments`, `/activity`, `/attachments`, `/neighbors`, `/favorite`; `/search`, `/search/ask`; `/exports`; `{base}/options`; `/mentions` |

Every lifecycle-enabled collection also implements `POST {id}/archive`, `POST {id}/restore`, `DELETE {id}` (soft), `POST /bulk-delete`, `DELETE {id}/purge`, `PATCH {id}/stage`, and `GET {base}/counts`.

Topic and meeting cards expose a permission-gated `⋯` menu with Delete. Delete is an auditable soft delete to `deleted` by default; permanent purge is a distinct privileged operation and is not exposed by the normal card menu.

Archive (`/archive`) currently aggregates by listing each source with `status=archived` and `status=deleted`. Those list filters are required; a dedicated `/archive` API is optional later.

## 8. Production acceptance checklist

- Every protected endpoint has server-side capability and tenant/ownership tests.
- Session cookies, CSRF, CORS, rate limits, request timeouts, and logout revocation are verified.
- Upload extension, detected MIME, size/count, malware, tenant, and storage policies are server enforced.
- Sensitive mutations and permission/configuration changes create immutable audit events.
- Search, schemas, exports, comments, attachments, and assignment options never reveal inaccessible data.
- API schemas and generated clients are contract-tested against the frontend adapters.
- Cache invalidation, permission revocation, duplicate message delivery, retries, and dead-letter recovery are integration-tested.
- Mock mode is disabled in deployed environments.

Related implementation guides: `frontend/docs/api-integration-guide.md` and `frontend/docs/local-frontend-docker-backend.md`.
