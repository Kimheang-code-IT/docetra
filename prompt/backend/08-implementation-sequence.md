# Backend Implementation Sequence

Build order for the FastAPI app. `backend/` already exists; remaining work is workers, domain tables, and cutover — not a greenfield skeleton.

Aligns three sources:

1. `prompt/specification/09-implementation-plan.md` (engineering phases)
2. `project-management/01-timeline-management.md` (24 Aug–13 Nov 2026 sprints)
3. Current frontend adapters (mock-complete, HTTP-ready)

**Planning baseline:** 18 August 2026. **API freeze gate:** 11 September 2026. **Planned release:** 13 November 2026.

---

## 1. Delivery window mapped to backend folders

| Sprint | Dates | Backend folders to create/fill | Frontend cutover proof |
| --- | --- | --- | --- |
| **S1 Control and contracts** | 24 Aug–4 Sep | `app/main.py`, `core/`, `db/`, `alembic/`, Dockerfile, OpenAPI stub, `tests/contract` | Paths in OpenAPI = `api-endpoints.ts`; CI typecheck/build still green |
| **S2 Identity and master data** | 7–18 Sep | `api/v2/auth.py`, `modules/identity`, `people_access`, `organization` | Login/me/logout/CSRF; departments/companies/officers/roles/users CRUD |
| **S3 Configurable records** | 21 Sep–2 Oct | `admin_config`, `modules/record`, `collaboration` | Record types/attributes; four record boards + document pages on HTTP |
| **S4 Meetings and collaboration** | 5–16 Oct | `modules/meetings`, `scheduler_jobs/`, Telegram meeting bot | Topic board, reorder, assign, notes, comments, APScheduler reminders |
| **S5 Portal and intelligence** | 19–30 Oct | `storage_integration`, `portal.py`, `search`, `reporting_support`, Drive jobs | Upload, logs, search, dashboard summary, exports |
| **S6 UAT and release** | 2–13 Nov | Hardening, password-reset email, Development Telegram bot, runbooks | `NUXT_PUBLIC_USE_MOCK_DATA=false` in staging/UAT; zero Blocker defects |

Epic owners from the timeline: Kimheang for E02–E04/E06; Vitou for E05; Sothay for E07; Vechika for E08.

---

## 2. Phase checklist (what “done” means)

### Phase A — Skeleton (Sprint 1)

- [ ] `backend/` tree from [`06-backend-file-structure.md`](./06-backend-file-structure.md)
- [ ] Settings load from `backend.env` (`core/config.py`)
- [ ] Error envelope `{ error: { code, message, fields, requestId } }`
- [ ] CORS allow-list = `CORS_ALLOWED_ORIGINS` (never `*` with credentials)
- [ ] Health/ready checks used by Compose
- [ ] Alembic can create empty schema + mixin tables
- [ ] Contract test: every `ApiEndpoints` path is listed (may 501 until implemented)

### Phase B — JWT cookies and permissions (Sprint 2 start)

- [x] JWT HttpOnly cookies + CSRF (`00-integration-contract.md` §2)
- [x] `/auth/login`, `/auth/me`, `/auth/refresh`, `/auth/logout`
- [ ] Flat `permissions` on `/auth/me`
- [ ] Capability catalog endpoint
- [ ] 401 vs 403 semantics the Nuxt dialogs already handle

### Phase C — Organization and users (Sprint 2)

- [ ] Five organization collections + `/options`
- [ ] Roles + users + officer link
- [ ] Mention search `{ id, label, type }`
- [ ] Archive/restore/delete/purge on master data where the UI exposes it

### Phase D — Configuration then records (Sprint 3)

- [ ] Record types, attributes, published schemas (long cache)
- [ ] Unified `record` + `record_detail`
- [ ] Four workflow boards: list, counts, stage PATCH, date range
- [ ] Document comments/activity/attachments/neighbors/favorites
- [ ] Record logs read model

### Phase E — Meetings (Sprint 4)

- [ ] Topics + history as record types
- [ ] Reorder and assign-topic
- [ ] Notes + Drive file link
- [ ] APScheduler process with PostgreSQL job store
- [ ] Reminder/start/end messages to RabbitMQ
- [ ] Lifecycle pauses/rebuilds schedules (`04-lifecycle-retention-and-collaboration.md`)

### Phase F — Portal, search, dashboard (Sprint 5)

- [ ] Multipart/signed upload with server MIME/size/malware checks
- [ ] Portal logs + system logs
- [ ] Drive sync jobs (partial UI is acceptable; API catalog `drive-files` is required)
- [ ] Search keyword/semantic + ask (permission-filtered)
- [ ] Dashboard summary (short cache)
- [ ] Export jobs `202` + poll

### Phase G — Notifications and release (Sprint 6)

- [ ] Forgot-password email (uniform response, hashed token)
- [ ] Change-password + avatar
- [ ] Meeting Telegram bot
- [ ] Development Telegram bot (private)
- [ ] Cache invalidation + DLQ recovery tests
- [ ] Mock mode off in deployed environments

Optional Google Sign-In / Calendar / Gmail stay behind [`05-google-workspace-integration.md`](./05-google-workspace-integration.md) and must not block v1.0.

---

## 3. Suggested first vertical slice

Do not implement all collections in parallel. First HTTP slice:

```text
POST /auth/login
GET  /auth/me
GET  /organizations/departments
POST /organizations/departments
PATCH /organizations/departments/{id}
GET  /organizations/departments/options
```

Then copy the entity mixin to officers → roles → users → record types → incoming documents → meetings.

---

## 4. Frontend switch

When a slice is ready locally:

```env
NUXT_PUBLIC_USE_MOCK_DATA=false
NUXT_PUBLIC_API_BASE=http://localhost:8000
NUXT_PUBLIC_AUTH_MODE=cookie
```

Pages must not change. If a field name mismatches, fix the Pydantic alias or the adapter type together.

---

## 5. Out of scope until named later

- Creating the `backend/` Python package in this prompt-only update
- Rewriting Nuxt pages to new URLs
- Microservices extraction
- Enabling Google Sign-In by default
- Using Redis or RabbitMQ as source of truth
