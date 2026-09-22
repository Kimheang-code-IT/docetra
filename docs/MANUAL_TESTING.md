# Docetra — Manual Testing Guide, Test Data & System Flow

Audience: QA, product, and operators doing manual acceptance testing of a running Docetra stack.
This document is self-contained: run the stack, create the data in the order below, then execute the test cases.

> UI labels are shown in English; the app also runs in Khmer (`en` / `km`). Where a value is user-typed, a
> Khmer suggestion is given in the format `English / ខ្មែរ`.

---

## 1. Environment & prerequisites

| Item | Value |
| --- | --- |
| App URL (single box) | `http://<server>:8080` (or `https://<domain>` behind host nginx) |
| API base | `http://<server>:8080/api/v2` |
| Health / readiness | `GET /health`, `GET /ready`, `GET /metrics` |
| Admin UI areas | Settings, Configuration, Organization, User Management, Portal |
| Roles | SuperAdmin, plus whatever roles you create |
| Supported browsers | Current Chrome / Edge / Firefox |

Before testing, make sure the stack is running and the app URL below opens the login page.
The first screen when the system has no users is the **Create administrator** setup form.

---

## 2. System flow

### 2.1 Processes (one codebase, four run modes)

```
                         ┌──────────────────────── nginx (:80 → HTTP_PORT) ───────────────────────┐
 browser ──HTTP(S)─────► │  static SPA (Nuxt, baked image)  +  reverse proxy /api, /health, /ready  │
                         └───────────────────────────────┬────────────────────────────────────────┘
                                                         │  /api/v2
                                                 ┌───────▼────────┐
                                                 │  api (FastAPI) │  + APScheduler (SCHEDULER_IN_API)
                                                 └─┬────┬─────┬───┘
                                                   │    │     │
                              ┌────────────────────┘    │     └───────────────────────┐
                              │                          │                             │
                       ┌──────▼──────┐            ┌──────▼──────┐               ┌──────▼──────┐
                       │ postgres    │            │ redis       │               │ rabbitmq    │
                       │ (truth)     │            │ (session +  │               │ (job queue) │
                       └─────────────┘            │  cache)     │               └──────┬──────┘
                                                  └─────────────┘                      │
                       ┌─────────────┐                                          ┌──────▼───────┐
                       │ minio / S3  │◄───────── attachments, exports, Drive ───│ worker       │
                       │ (objects)   │                                          │ (consumers)  │
                       └─────────────┘                                          └──────────────┘
                       ┌──────────────────────┐
                       │ telegram (bot proc)  │  long polling; separate container
                       └──────────────────────┘
```

- **api** — all HTTP (`/api/v2`), runs DB migrations on start (`alembic upgrade head`), optionally hosts the scheduler.
- **worker** — RabbitMQ consumers: outbox publish, Drive sync, exports, notifications.
- **scheduler** — APScheduler: meeting reminders, reconcile, export cleanup (in-API when `SCHEDULER_IN_API=true`).
- **telegram** — dedicated long-polling bot process.
- The API never runs background jobs; jobs go through the **transactional outbox → RabbitMQ → worker**.

### 2.2 Request flow (a mutation)

```
Browser → useApi() → /api/v2/<resource>
   → CSRF check → session cookie auth → Router
   → Application Workflow/Service (business rules, no commit)
   → Repository (SQL, flush)
   → Workflow commits, writes AuditLog + Outbox row (same transaction)
   → response { data, meta } envelope
Outbox → RabbitMQ → worker → side effects (email, Telegram, Drive, exports)
```

### 2.3 Authentication & first-run setup

```
GET /api/v2/auth/bootstrap → { needsSetup: true }        (count(users) == 0)
/login page switches to "Create administrator" form
POST /api/v2/auth/register  → first user = SuperAdmin, all permissions, session cookie set
logout / refresh            → cookie sessions (HttpOnly); tokens never in JSON by default
```

- After the first user exists, `/auth/register` closes (403).
- `SuperAdmin` (and `Admin`) role names bypass per-permission checks (`is_unrestricted`).
- CSRF uses a double-submit header (`X-CSRF-Token`) on mutating verbs.

### 2.4 Module boundaries (enforced)

```
reporting_support → record, organization, people_access, storage_integration
storage_integration → record, admin_config
record → organization, people_access, admin_config
organization → admin_config
people_access → admin_config
admin_config → (none)
```

`core`, `shared`, `integrations`, `platform` import no business module. Cross-module calls go through
`service` / `schema` / `exceptions` / `dependencies` facades only.

### 2.5 Record domain & surfaces

- One `record` domain, differentiated by `record_type` (code). Meetings are a record type, not a separate domain.
- A record type drives: fields/attributes, workflow stages, numbering, features, card display, menu/route surface.
- Built-in **codes** decide the surface:
  - `meeting_topic` → meeting surface (topic container), route `/meetings/topics`
  - `meeting_history` → meeting surface, timeline view, route `/meetings/history`
  - `incoming_document`, `outgoing_document`, `document`, `master_list_request` → document surface, `/records/<slug>`
  - any other code → document surface with a generated slug.
- Sidebar menus and routes are derived from **active record types**, not hard-coded.

### 2.6 Meetings (topic container)

```
meeting_topic (parent) ──1..n──► meeting_history (child)
   topic: title, description, date, child meetings
   meeting: title, letter number, date, mode, location,
            participants (officers), internal units (departments), external units (companies),
            notes/content, tags, stage
Board view: drag meeting between workflow stages (records transition permission).
```

### 2.7 Portal

- **File Upload** — upload files (Uppy) → stored in MinIO/S3 via the default storage provider (env fallback).
  Shows the active storage ("Storing on MinIO"), and blocks upload with a warning when storage is not configured.
- **Google Drive Sync** — blocked with a warning until a Google Drive provider is configured.
  Sync jobs are queued via outbox → worker.

### 2.8 Storage configuration (Settings → App Config)

- Tabs **Localization, Email, Telegram, Notifications, Security, Amazon S3, Google Drive**.
- **Amazon S3** tab (also used for MinIO): region, bucket, endpoint, public URL, access key, secret key,
  options (name/active/access mode/max size/allowed types/upload path), connection test.
- **Google Drive** tab: client id, client secret, folder id, sync schedule, connection test.
- A configured provider wins; otherwise the env MinIO (`S3_*`) is used.

### 2.9 Exports

```
Export dialog → POST /api/v2/exports (format csv | xlsx, scope, date range, fields)
   → outbox → worker → rows by resource + date filter
   → CSV (UTF-8 BOM) or Excel filled from template app/resources/export_templates/<resource>.xlsx
   → stored in MinIO, download via /api/v2/files/{jobId}
```

Excel template contract: first sheet, **header row 1**; each header cell is matched to a field by its label
(or field code); data rows are appended from row 2; unmatched columns stay blank.

### 2.10 Audit, history, concurrency

- Every significant mutation writes an `AuditLog`; history is append-only.
- Records use optimistic concurrency: `version` + `If-Match`.
- Audit views: `/records/logs`, `/portal/portal-logs`, `/system-monitor/system-logs`.

---

## 3. Roles & permissions quick reference

Permission prefix → area (matrix shown in Role editor):

| Area | Prefix | Actions (typical) |
| --- | --- | --- |
| Dashboard | `dashboard` | view |
| Archive | `archive` | view |
| Record logs | `records.logs` | view, export |
| Departments | `organizations.departments` | view, create, edit, delete, export, comment |
| Companies | `organizations.companies` | same |
| Purposes | `organizations.purposes` | same |
| Sectors | `organizations.sectors` | same |
| Officers | `organizations.officers` | same |
| Users | `users.users` | view, create, edit, archive, restore, delete, purge, comment, configure |
| Roles | `users.roles` | same |
| Record types | `configuration.record_types` | view, create, edit, delete, export, comment, configure |
| Attributes | `configuration.record_attributes` | same |
| Per record type | `records.<type>` | view, create, edit, archive, restore, delete, purge, assign, share, export, comment, transition |
| File upload | `portal.file_upload` | view, create, delete, share, export |
| Google Drive sync | `portal.google_drive_sync` | view, create, edit, delete, export, comment, configure |
| Portal logs | `portal.logs` | view, export |
| System logs | `system.logs` | view, export |
| App info | `settings.app_info` | view, edit, configure |
| App config | `settings.app_config` | view, edit, configure |
| Storage | `settings.storage` | view, edit, configure |

`View` is a prerequisite for every other action on the same row.

---

## 4. Full manual test data (create in this order)

Create everything as the SuperAdmin. Order matters: references must exist before they are used.
The tables below are **the complete data set** — enter them top-to-bottom in each section.

Format: `English / ខ្មែរ` when a Khmer display is useful.

**Testing flow (recommended order)**

1. Open the app URL and confirm the login/setup screen loads.
2. Create the first administrator (Step 0).
3. Complete Settings: App Info, then App Config (localization, email, Telegram, notifications, security, Amazon S3, Google Drive).
4. Configure the system: Attributes first (Step 6), then Record Types (Step 7).
5. Create organization reference data: departments → companies → purposes → sectors (Step 3), then officers (Step 4).
6. Create roles, then users linked to officers (Step 5).
7. Create records in each document type (Step 8).
8. Create meeting topics, then meetings under them (Step 9).
9. Exercise the Portal: file uploads and Google Drive sync (Step 10).
10. Run cross-cutting checks: search, dashboard, logs, archive, language switch, exports (Step 11).
11. Finish with negative/boundary cases (Step 12), then the test cases in Section 6.

### Step 0 — First administrator (setup form)

| Field | Value |
| --- | --- |
| Name | `System Administrator` / `អ្នកគ្រប់គ្រងប្រព័ន្ធ` |
| Email | `admin@example.com` |
| Password | `Admin@12345` |
| Confirm password | `Admin@12345` |

Expected: lands on Dashboard, sidebar shows all groups, role = SuperAdmin.

### Step 1 — App Info (Settings → App Info)

| Field | Value |
| --- | --- |
| Application name | `Docetra` / `ឌូសេត្រា` |
| Description | `Administrative record management platform` |
| Support email | `support@example.com` |
| Support phone | `+855 23 000 000` |
| Website | `https://example.com` |
| Address | `#12, Preah Norodom Blvd, Phnom Penh` |
| Copyright | `© 2026 Example Org` |
| Primary color | `#e8472a` |
| Daily quote/tagline | `One source of truth for records` |

### Step 2 — App Config (Settings → App Config)

**Localization**

| Field | Value |
| --- | --- |
| Default landing page | Dashboard |
| Default page size | 20 |
| Default record view | Table |
| Default language | English |
| Available languages | English, Khmer |
| Timezone | `Asia/Phnom_Penh` |
| Date format | `DD/MM/YYYY` |
| Time format | `24h` |
| First day of week | Monday |
| Number format | `1,234.56` |
| Currency | `USD` |
| Locale | `en-US` |

**Email** (optional — needed for password reset in production)

| Field | Value |
| --- | --- |
| Enabled | on |
| SMTP host | `smtp.example.com` |
| SMTP port | `587` |
| Username | `no-reply@example.com` |
| Password | `••••••` |
| Encryption | `STARTTLS` |
| From name | `Docetra` |
| From email | `no-reply@example.com` |
| Reply-to | `support@example.com` |

**Telegram** (optional)

| Field | Value |
| --- | --- |
| Enabled | on |
| Bot display name | `Docetra Bot` |
| Bot token | `123456:ABC-DEF...` |
| Bot username | `@docetra_bot` |
| Message language | Khmer |
| Include record link | on |
| Include organization | on |
| Include assigned officer | on |
| Message template | `[{{record_type}}] {{record_number}} — {{record_title}}\nStatus: {{status}} · {{stage}}\n{{record_url}}` |

**Notifications**

| Field | Value |
| --- | --- |
| In-app | on |
| Email channel | on |
| Telegram channel | on |
| Delivery retries | `3` |
| Meeting reminder offsets | `1440,60,15` |
| Meeting recurrence horizon (days) | `90` |

**Security**

| Field | Value |
| --- | --- |
| Session timeout (minutes) | `480` (prod `15`) |
| Max login attempts | `5` |
| Account lock (minutes) | `15` |
| Password expiry (days) | `0` (never) |
| Audit retention (days) | `365` |
| Require password change | off |
| Allowed upload extensions | `pdf,doc,docx,xls,xlsx,png,jpg,jpeg,gif,webp,txt,csv` |

**Amazon S3 tab** (MinIO example; also used for S3)

| Field | Value |
| --- | --- |
| Name | `MinIO local` |
| Region | `us-east-1` |
| Bucket | `docetra` |
| Endpoint | `http://minio:9000` |
| Public URL | `http://localhost:9000/docetra` |
| Access key | `docetra` |
| Secret key | *(value of `MINIO_ROOT_PASSWORD`)* |
| Active | on |
| Access mode | `Private` |
| Max file size (MB) | `25` |
| Allowed extensions | `pdf,docx,xlsx,png,jpg,jpeg,gif,webp,txt,csv` |
| Upload path pattern | `uploads/{yyyy}/{mm}/{uuid}` |

Click **Test connection** → expect `Connected to docetra`.

**Google Drive tab** (only if you have credentials)

| Field | Value |
| --- | --- |
| Name | `Google Drive` |
| Client id | `xxx.apps.googleusercontent.com` |
| Client secret | `••••` |
| Folder id | `1AbCdEfGhIjKlMnOpQrStUvWxYz` |
| Sync schedule | daily |
| Active | on |

### Step 3 — Organization reference

**Departments** (`/organizations/departments`) — create parents first

| Name | Code | Parent |
| --- | --- | --- |
| Executive Office / ទីស្តីការគណៈរដ្ឋមន្ត្រី | `EXEC` | — |
| Administration / រដ្ឋបាល | `ADM` | Executive Office |
| Finance / ហិរញ្ញវត្ថុ | `FIN` | Executive Office |
| Human Resources / ធនធានមនុស្ស | `HR` | Administration |
| Procurement / លទ្ធកម្ម | `PRC` | Finance |
| Technical / បច្ចេកទេស | `TEC` | Executive Office |
| IT Support / ជំនួយព័ត៌មានវិទ្យា | `ITS` | Technical |
| Infrastructure / ហេដ្ឋារចនាសម្ព័ន្ធ | `INF` | Technical |
| Legal / នីតិកម្ម | `LEG` | Executive Office |
| Communications / ទំនាក់ទំនង | `COM` | Executive Office |
| Internal Audit / សវនកម្មផ្ទៃក្នុង | `AUD` | Executive Office |

**Companies** (`/organizations/companies`)

| Name | Code | Sector | Contact email | Phone |
| --- | --- | --- | --- | --- |
| Acme Co., Ltd | `ACME` | Private | `contact@acme.example` | `+855 12 111 111` |
| Global Tech | `GTECH` | Technology | `hello@gtech.example` | `+855 12 222 222` |
| Sunrise Trading | `SUN` | Private | `sales@sunrise.example` | `+855 12 333 333` |
| Mekong Logistics | `MEK` | Private | `ops@mekong.example` | `+855 12 444 444` |
| Angkor Supplies | `ANG` | Private | `info@angkor.example` | `+855 12 555 555` |
| DataSoft Solutions | `DSO` | Technology | `support@datasoft.example` | `+855 12 666 666` |
| Premier Consulting | `PREM` | Private | `contact@premier.example` | `+855 12 777 777` |
| Ocean Freight | `OCEAN` | Private | `freight@ocean.example` | `+855 12 888 888` |
| Green Energy | `GREEN` | Private | `power@green.example` | `+855 12 999 999` |
| National Printing | `NPRINT` | Private | `print@nprint.example` | `+855 12 000 000` |

**Purposes** (`/purpose`)

| Name | Code |
| --- | --- |
| Correspondence | `CORR` |
| Procurement | `PROC` |
| Internal Memo | `MEMO` |
| Legal Notice | `LEGAL` |
| Budget Request | `BUD` |
| HR Request | `HRREQ` |
| IT Support | `ITSUP` |
| Contract Review | `CONT` |
| Report Submission | `RPT` |
| Public Notice | `PUBN` |

**Sectors** (`/sector`)

| Name | Code |
| --- | --- |
| Public | `PUB` |
| Private | `PRI` |
| NGO | `NGO` |
| Education | `EDU` |
| Health | `HLT` |
| Finance | `FIN` |
| Technology | `TECH` |
| Construction | `CONST` |

### Step 4 — Officers (`/officers`)

| Name | Email | Department | Role |
| --- | --- | --- | --- |
| Sok Dara / សុខ ដារា | `dara@example.com` | Executive Office | SuperAdmin |
| Chan Vanna / ចាន់ វណ្ណា | `vanna@example.com` | Finance | Manager |
| Ly Pisey / លី ពិសី | `pisey@example.com` | Technical | Officer |
| Kim Sopheak / គីម សុភាព | `sopheak@example.com` | Administration | Manager |
| Meas Chanthy / មាស ចន្ធី | `chanthy@example.com` | Human Resources | Officer |
| Pich Sokha / ពេជ្រ សុខា | `sokha@example.com` | Procurement | Clerk |
| Nou Rithy / នូ រិទ្ធី | `rithy@example.com` | IT Support | Officer |
| Seng Bopha / សេង បុប្ផា | `bopha@example.com` | Legal | Manager |
| Ouk Sreyleak / អ៊ុក ស្រីលក្ខ | `sreyleak@example.com` | Communications | Clerk |
| Tep Samnang / ទេព សំណាង | `samnang@example.com` | Infrastructure | Officer |
| Rin Chhaya / រិន ឆាយា | `chhaya@example.com` | Internal Audit | Auditor |
| Hang Dara / ហង់ ដារា | `hang@example.com` | Finance | Clerk |
| Phan Vuthy / ផាន់ វុទ្ធី | `vuthy@example.com` | Technical | Officer |
| Chea Molika / ជា មុនីកា | `molika@example.com` | Administration | Officer |

### Step 5 — Roles & Users

**Roles** (`/user-management/roles`) — edit the permission matrix; create after attributes/types if record permissions are not yet listed

| Role | Description | Permission rows |
| --- | --- | --- |
| Executive | Executive oversight | all `view` + record `edit`, `export`, `transition` |
| Manager | Department manager | all `view` + record `create`, `edit`, `assign`, `comment`, `export`, `transition` |
| Officer | Staff | `dashboard.view`, `archive.view`, record `view`, `create`, `edit`, `comment` |
| Clerk | Data entry | `dashboard.view`, record `view`, `create`, `comment`, `portal.file_upload.view/create` |
| Viewer | Read only | `dashboard.view`, `archive.view`, record `view` |
| Auditor | Audit/read | all `view`, `records.logs.view/export`, `portal.logs.view/export`, `system.logs.view/export` |

**Users** (`/user-management/users`) — link each to its officer

| Name | Email | Password | Role | Officer |
| --- | --- | --- | --- | --- |
| Chan Vanna | `vanna@example.com` | `Vanna@12345` | Manager | Chan Vanna |
| Ly Pisey | `pisey@example.com` | `Pisey@12345` | Officer | Ly Pisey |
| Kim Sopheak | `sopheak@example.com` | `Sopheak@12345` | Manager | Kim Sopheak |
| Meas Chanthy | `chanthy@example.com` | `Chanthy@12345` | Officer | Meas Chanthy |
| Pich Sokha | `sokha@example.com` | `Sokha@12345` | Clerk | Pich Sokha |
| Nou Rithy | `rithy@example.com` | `Rithy@12345` | Officer | Nou Rithy |
| Seng Bopha | `bopha@example.com` | `Bopha@12345` | Manager | Seng Bopha |
| Ouk Sreyleak | `sreyleak@example.com` | `Sreyleak@12345` | Clerk | Ouk Sreyleak |
| Tep Samnang | `samnang@example.com` | `Samnang@12345` | Officer | Tep Samnang |
| Rin Chhaya | `chhaya@example.com` | `Chhaya@12345` | Auditor | Rin Chhaya |
| Hang Dara | `hang@example.com` | `Hang@12345` | Clerk | Hang Dara |
| Phan Vuthy | `vuthy@example.com` | `Vuthy@12345` | Officer | Phan Vuthy |
| Chea Molika | `molika@example.com` | `Molika@12345` | Officer | Chea Molika |

### Step 6 — Attributes (Configuration → Attributes)

Create one attribute per data type so every field renderer can be tested.

| # | Label | Code | Data type | Options / notes |
| --- | --- | --- | --- | --- |
| 1 | Priority | `priority` | select | Low, Normal, High, Urgent (Urgent = red) |
| 2 | Status note | `status_note` | short_text | max 120 |
| 3 | Summary | `summary` | long_text | max 500 |
| 4 | Body | `body` | rich_text | — |
| 5 | Quantity | `quantity` | integer | min 0 |
| 6 | Amount | `amount` | decimal | precision 2 |
| 7 | Budget | `budget` | currency | USD |
| 8 | Confidential | `confidential` | boolean | — |
| 9 | Due date | `due_date` | date | allow future |
| 10 | Reminder time | `reminder_time` | time | — |
| 11 | Scheduled at | `scheduled_at` | datetime | — |
| 12 | Contact email | `contact_email` | email | — |
| 13 | Contact phone | `contact_phone` | phone | — |
| 14 | Reference link | `reference_link` | url | — |
| 15 | Category | `category` | select | General, Legal, Finance, HR, IT |
| 16 | Tags | `tags` | multi_select | urgent, external, internal, follow-up, archive |
| 17 | Approval | `approval` | radio | approved, rejected, pending |
| 18 | Channels | `channels` | checkbox_group | email, telegram, in-app |
| 19 | Scanned file | `scanned_file` | file | pdf,docx |
| 20 | Photo | `photo` | image | png,jpg,webp |
| 21 | Responsible unit | `responsible_unit` | organization | departments |
| 22 | Assigned officer | `assigned_officer` | officer | — |
| 23 | Requester user | `requester_user` | user | — |
| 24 | Related record | `related_record` | record_reference | — |

On #1, #15, #16, #17, #18 set required, searchable, filterable, sortable, show-in-list as appropriate.

### Step 7 — Record types (Configuration → Record Types)

Create these **with the exact code** so the correct surface and menus appear.

| Name | Code | Icon | Color | Features | Attributes |
| --- | --- | --- | --- | --- | --- |
| Meeting Topic | `meeting_topic` | calendar | #6366f1 | workflow, attachments, comments | priority |
| Meeting | `meeting_history` | calendar-clock | #0ea5e9 | workflow, attachments, comments, assignment | priority, due_date |
| Incoming Document | `incoming_document` | file-input | #10b981 | workflow, attachments, assignment | priority, category, due_date, confidential |
| Outgoing Document | `outgoing_document` | file-output | #f59e0b | workflow, attachments, assignment | priority, category, due_date |
| Document | `document` | file-text | #64748b | workflow, comments | priority, category, body |
| Master List Request | `master_list_request` | list-checks | #8b5cf6 | workflow, comments | priority, due_date |
| Contract | `contract` | file-signature | #ef4444 | workflow, attachments, assignment | amount, budget, due_date, approval |
| Invoice | `invoice` | receipt | #14b8a6 | workflow, attachments | amount, due_date, approval |

Default workflow stages are auto-filled: document types → `Created → Record created → … → Finished / Final`;
meeting types → `Intake → Review → Approval → Completed`. Adjust stages in the Workflow tab if desired.

### Step 8 — Records (documents) — 24 rows

Create each in its type's workspace (New → fill → Save), then move some through stages.

**Incoming Document** (`incoming_document`)

| # | Title | Stage | Priority | Category | Due date | Confidential |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Purchase request from Acme | Submitted to director | High | Finance | 2026-03-15 | off |
| 2 | Ministry directive 012/26 | Record created | Normal | Legal | 2026-03-20 | on |
| 3 | Supplier quotation — Sunrise | Observation note | Normal | Finance | 2026-03-18 | off |
| 4 | Partner agreement — Global Tech | Waiting related document | High | Legal | 2026-03-25 | on |
| 5 | Request for IT equipment | Record created | Low | IT | 2026-04-02 | off |
| 6 | Audit findings response | Submitted to DDG | High | General | 2026-03-30 | on |

**Outgoing Document** (`outgoing_document`)

| # | Title | Stage | Priority | Category | Due date |
| --- | --- | --- | --- | --- | --- |
| 1 | Reply to Acme quotation | Reply | Normal | Finance | 2026-03-10 |
| 2 | Notification to supplier | Record created | Normal | General | 2026-03-12 |
| 3 | Contract approval letter | Submitted to DG | High | Legal | 2026-03-22 |
| 4 | Budget request to ministry | Submitted to director | High | Finance | 2026-04-01 |
| 5 | IT maintenance notice | Record created | Low | IT | 2026-03-28 |
| 6 | Public notice — road works | Finished / Final | Normal | General | 2026-02-28 |

**Document** (`document`)

| # | Title | Stage | Priority | Category |
| --- | --- | --- | --- | --- |
| 1 | Internal memo — office move | Created | Low | General |
| 2 | HR policy update 2026 | Further measures | Normal | HR |
| 3 | Procurement guidelines v3 | Record created | Normal | Finance |
| 4 | Disaster recovery plan | Observation note | High | IT |
| 5 | Annual report draft | Submitted to director | Normal | General |

**Master List Request** (`master_list_request`)

| # | Title | Stage | Priority | Due date |
| --- | --- | --- | --- | --- |
| 1 | Update supplier master list | Review | Normal | 2026-04-01 |
| 2 | Add new department codes | Intake | Low | 2026-04-05 |
| 3 | Clean duplicate companies | Approval | High | 2026-03-31 |
| 4 | Update purpose catalog | Completed | Normal | 2026-03-20 |

**Contract** (`contract`)

| # | Title | Stage | Amount | Approval |
| --- | --- | --- | --- | --- |
| 1 | Maintenance contract — DataSoft | Review | `12,000.00` | pending |
| 2 | Supply contract — Angkor Supplies | Approval | `8,500.00` | approved |

**Invoice** (`invoice`)

| # | Title | Stage | Amount | Approval |
| --- | --- | --- | --- | --- |
| 1 | INV-2026-001 — Green Energy | Created | `1,250.00` | pending |
| 2 | INV-2026-002 — Ocean Freight | Record created | `640.00` | approved |

### Step 9 — Meetings & topics

**Topics** (`/meetings/topics`) — 8

| Title | Date | Description |
| --- | --- | --- |
| Monthly coordination | 2026-02-10 | Cross-department monthly sync |
| Budget review Q1 | 2026-02-18 | Q1 budget review |
| HR policy refresh | 2026-02-20 | HR policy updates 2026 |
| Procurement planning | 2026-03-02 | Q2 procurement plan |
| IT infrastructure | 2026-03-05 | Network/server upgrade |
| Legal compliance | 2026-03-09 | Compliance checklist |
| Communications strategy | 2026-03-12 | Public notice plan |
| Audit follow-up | 2026-03-16 | Audit action items |

**Meetings** (`/meetings/history`) — 18 (assign to a topic, set mode/location/participants)

| # | Title | Letter no. | Date/time | Mode | Location | Participants | Topic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Monthly coordination — January | MTG-2026-001 | 2026-01-13 09:00 | in_person | Meeting room A | Sok Dara, Chan Vanna, Ly Pisey | Monthly coordination |
| 2 | Monthly coordination — February | MTG-2026-002 | 2026-02-10 09:00 | in_person | Meeting room A | Sok Dara, Chan Vanna | Monthly coordination |
| 3 | Budget review Q1 — session 1 | MTG-2026-003 | 2026-02-18 14:00 | online | Zoom | Sok Dara, Ly Pisey | Budget review Q1 |
| 4 | Budget review Q1 — session 2 | MTG-2026-004 | 2026-02-19 10:00 | hybrid | Meeting room B | Chan Vanna, Hang Dara | Budget review Q1 |
| 5 | HR policy refresh — kickoff | MTG-2026-005 | 2026-02-20 09:30 | in_person | Meeting room C | Kim Sopheak, Meas Chanthy | HR policy refresh |
| 6 | HR policy refresh — review | MTG-2026-006 | 2026-02-25 15:00 | online | Google Meet | Meas Chanthy | HR policy refresh |
| 7 | Procurement planning — suppliers | MTG-2026-007 | 2026-03-02 08:30 | in_person | Meeting room A | Pich Sokha, Chan Vanna | Procurement planning |
| 8 | Procurement planning — approvals | MTG-2026-008 | 2026-03-04 14:00 | hybrid | Meeting room B | Pich Sokha | Procurement planning |
| 9 | IT infrastructure — network | MTG-2026-009 | 2026-03-05 09:00 | in_person | Server room | Nou Rithy, Tep Samnang | IT infrastructure |
| 10 | IT infrastructure — security | MTG-2026-010 | 2026-03-06 11:00 | online | Zoom | Nou Rithy, Phan Vuthy | IT infrastructure |
| 11 | Legal compliance — checklist | MTG-2026-011 | 2026-03-09 10:00 | in_person | Meeting room C | Seng Bopha | Legal compliance |
| 12 | Legal compliance — sign-off | MTG-2026-012 | 2026-03-11 16:00 | hybrid | Meeting room A | Seng Bopha, Sok Dara | Legal compliance |
| 13 | Communications strategy — plan | MTG-2026-013 | 2026-03-12 09:00 | in_person | Meeting room B | Ouk Sreyleak | Communications strategy |
| 14 | Communications strategy — review | MTG-2026-014 | 2026-03-13 14:30 | online | Google Meet | Ouk Sreyleak, Kim Sopheak | Communications strategy |
| 15 | Audit follow-up — action items | MTG-2026-015 | 2026-03-16 08:00 | in_person | Meeting room A | Rin Chhaya, Sok Dara | Audit follow-up |
| 16 | Audit follow-up — evidence | MTG-2026-016 | 2026-03-17 10:00 | hybrid | Meeting room C | Rin Chhaya | Audit follow-up |
| 17 | Ad-hoc — urgent purchase | MTG-2026-017 | 2026-03-18 13:00 | in_person | Meeting room B | Chan Vanna, Pich Sokha | Procurement planning |
| 18 | Ad-hoc — system downtime | MTG-2026-018 | 2026-03-19 09:00 | online | Zoom | Nou Rithy, Sok Dara | IT infrastructure |

Also set **internal units** (departments) and **external units** (companies) on at least 3 meetings, and add notes/tags.

### Step 10 — Portal

**File Upload** (`/portal/file-upload`) — 12 uploads

| # | File name | Type | Size (approx) |
| --- | --- | --- | --- |
| 1 | `report-q1.pdf` | PDF | 1.2 MB |
| 2 | `directive-012.pdf` | PDF | 800 KB |
| 3 | `quotation-sunrise.docx` | DOCX | 240 KB |
| 4 | `budget-2026.xlsx` | XLSX | 320 KB |
| 5 | `photo-office.png` | PNG | 1.5 MB |
| 6 | `photo-team.jpg` | JPG | 2.1 MB |
| 7 | `supplier-list.csv` | CSV | 45 KB |
| 8 | `notes-meeting.txt` | TXT | 6 KB |
| 9 | `logo-national.svg` | SVG | 12 KB |
| 10 | `contract-draft.docx` | DOCX | 180 KB |
| 11 | `audit-evidence.pdf` | PDF | 940 KB |
| 12 | `export-sample.csv` | CSV | 20 KB |

Verify each row shows name, size, date and downloads via `/api/v2/files/{id}`.

**Google Drive Sync** (`/portal/google-drive-sync`) — sources

| # | Source name | Folder id | Schedule |
| --- | --- | --- | --- |
| 1 | Official documents | `1AbCdEfGhIjKlMnOpQrStUvWxYz` | daily |
| 2 | Finance shared | `1ZzYyXxWwVvUuTtSsRrQqPpOoNn` | weekly |
| 3 | HR shared | `1MmNnOoPpQqRrSsTtUuVvWwXxYy` | manual |

Run a sync on source #1 and confirm the job queues → completes and its files appear.

**Portal Logs** (`/portal/portal-logs`): confirm entries for uploads and Drive sync.

### Step 11 — Cross-cutting pages

- **Dashboard**: KPIs/counts reflect the created records and meetings.
- **Search** (top bar): search `Acme`, `MTG-2026`, `Bopha`, `invoice`.
- **Records Logs** (`/records/logs`): create/edit/transition entries with actor + time.
- **Archive**: archive one document → leaves the active list, appears in Archive; restore it.
- **System Monitor → System Logs** (`/system-monitor/system-logs`): worker/outbox/system entries.
- **Language**: switch EN ⇄ KM — sidebar, forms, dialogs, and built-in record type labels translate.
- **Export**: from each list, Export → CSV and Excel (.xlsx) with a date range and fields; download both.

### Step 12 — Negative / boundary data

| Case | Input | Expected |
| --- | --- | --- |
| Duplicate code | Create a Company with an existing code | Validation error (unique) |
| Missing required | Department with empty name | Validation error |
| Self parent | Department parent = itself | Rejected ("cannot be own ancestor") |
| Bad email | Officer email `not-an-email` | Validation error |
| Short password | User password `123` | Validation error (min length) |
| Oversize upload | File > max size | Upload rejected |
| Disallowed extension | Upload `.exe` | Rejected (415) |
| Reversed dates | Export end date before start date | "End date must be on or after start date" |
| Empty export fields | Uncheck all fields | "Select at least one field" |
| Closed registration | `POST /auth/register` after setup | `403 Registration is closed` |

---

## 5. Field-by-field input matrix (every page + all conditional fields)

Enter **every** field below. "Condition" tells you when a field/control appears — test both the shown and hidden state.

### 5.1 Auth pages

**Login** (`/auth/login`)

| Field | Type | Input | Condition / notes |
| --- | --- | --- | --- |
| Email | email | `admin@example.com` | required |
| Password | password | `Admin@12345` | required |
| Remember me | checkbox | on | only in login mode (hidden in setup mode) |
| Forgot password | link | — | only in login mode |
| Locale switch | select | EN / KM | always |

**First-run setup** (same page, setup mode — shown only when no users exist)

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| Name | text | `System Administrator` | setup only |
| Email | email | `admin@example.com` | setup only |
| Password | password | `Admin@12345` | setup only, min 8 |
| Confirm password | password | `Admin@12345` | setup only, must match |

**Forgot password** (`/auth/forget-password` → `/auth/verify-code` → `/auth/reset-password`)

| Step | Field | Type | Input |
| --- | --- | --- | --- |
| Request | Email | email | `vanna@example.com` |
| Verify | Code | text (6 digits) | dev shows `debugCode` in the response |
| Reset | Password | password | `Vanna@99999` |
| Reset | Confirm password | password | `Vanna@99999` |

**Change password / Profile** (user menu)

| Field | Type | Input |
| --- | --- | --- |
| Current password | password | `Admin@12345` |
| New password | password | `Admin@54321` |
| Confirm password | password | `Admin@54321` |
| Avatar | image upload | `photo-team.jpg` (≤ 2 MB) |

### 5.2 Settings → App Info

| Field | Type | Input |
| --- | --- | --- |
| Application name | text | `Docetra` / `ឌូសេត្រា` |
| Description | textarea | `Administrative record management platform` |
| Support email | text | `support@example.com` |
| Support phone | text | `+855 23 000 000` |
| Website | url | `https://example.com` |
| Address | text | `#12, Preah Norodom Blvd, Phnom Penh` |
| Copyright | text | `© 2026 Example Org` |
| Primary color | color | `#e8472a` |
| Logo | image | `logo-national.svg` |

### 5.3 Settings → App Config (every tab)

**Localization**

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| Default landing page | select | Dashboard | — |
| Default page size | select | 20 | — |
| Default record view | select | Table | — |
| Default language | select | English | — |
| Available languages | multiselect | English, Khmer | — |
| Timezone | select | `Asia/Phnom_Penh` | — |
| Date format | select | `DD/MM/YYYY` | — |
| Time format | select | `24h` | — |
| First day of week | select | Monday | — |
| Number format | select | `1,234.56` | — |
| Currency | select | `USD` | — |
| Locale | select | `en-US` | — |

**Email**

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| Enabled | boolean | on | — |
| SMTP host | text | `smtp.example.com` | shown when enabled |
| SMTP port | number | `587` | shown when enabled |
| Username | text | `no-reply@example.com` | enabled |
| Password | secret | `••••••` | enabled |
| Encryption | select | STARTTLS | enabled |
| From name | text | `Docetra` | enabled |
| From email | text | `no-reply@example.com` | enabled |
| Reply-to | text | `support@example.com` | enabled |
| Connection status | connection-status | — | always |

**Telegram**

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| Enabled | boolean | on | — |
| Bot display name | text | `Docetra Bot` | shown when enabled |
| Bot token | secret | `123456:ABC-DEF...` | enabled |
| Bot username | text | `@docetra_bot` | enabled |
| Message language | select | Khmer | enabled |
| Include record link | boolean | on | enabled |
| Include organization | boolean | on | enabled |
| Include assigned officer | boolean | on | enabled |
| Message template | textarea | `[{{record_type}}] {{record_number}} …` | enabled |
| Destinations | builder | one chat + one group | enabled |
| Connection status | connection-status | — | always |

**Notifications**

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| In-app | boolean | on | — |
| Email channel | boolean | on | requires Email enabled |
| Telegram channel | boolean | on | requires Telegram enabled |
| Delivery retries | number | `3` | — |
| Meeting reminder offsets | csv-list | `1440,60,15` | — |
| Meeting recurrence horizon | number | `90` | — |
| Event rules | builder | one rule per event | — |

**Security**

| Field | Type | Input |
| --- | --- | --- |
| Session timeout (min) | number | `480` |
| Max login attempts | number | `5` |
| Account lock (min) | number | `15` |
| Password expiry (days) | number | `0` |
| Audit retention (days) | number | `365` |
| Require password change | boolean | off |
| Allowed upload extensions | csv-list | `pdf,doc,docx,xls,xlsx,png,jpg,jpeg` |

**Amazon S3** (also MinIO)

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| **Create provider** button | action | — | shown when no provider for this tab |
| Name | text | `MinIO local` | after provider exists |
| Region | select | `us-east-1` | provider |
| Bucket | text | `docetra` | provider |
| Endpoint | text | `http://minio:9000` | provider |
| Public URL | url | `http://localhost:9000/docetra` | provider |
| Access key | text | `docetra` | provider |
| Secret key | secret | `••••••` | provider |
| Active | boolean | on | provider |
| Access mode | select | Private | provider |
| Max file size (MB) | number | `25` | provider |
| Allowed extensions | csv-list | `pdf,docx,xlsx,png,jpg` | provider |
| Upload path pattern | text | `uploads/{yyyy}/{mm}/{uuid}` | provider |
| Connection test / Activate / Set default / Delete | actions | — | Test shown when provider exists; Delete hidden for default |

**Google Drive**

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| **Create provider** button | action | — | shown when no provider |
| Name | text | `Google Drive` | provider |
| Client id | text | `xxx.apps.googleusercontent.com` | provider |
| Client secret | secret | `••••` | provider |
| Folder id | text | `1AbCdEfGhIjKlMnOpQrStUvWxYz` | provider |
| Sync schedule | select | daily | provider |
| Options (name/active/access mode/max size/allowed types/path) | mixed | as S3 | provider |
| Connection test / Activate / Set default / Delete | actions | — | provider |

### 5.4 Configuration → Attributes

**Basic tab**

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| Label | text | `Urgent reason` | required |
| Code | text | `urgent_reason` | required; read-only when editing |
| Description | textarea | `Why the item is urgent` | — |
| Help text | text | `Shown under the field` | — |
| Data type | select | `short_text` | required |
| Placeholder | text | `Type a reason` | — |
| Status | select | Active | — |

**Field tab:** Required, Unique, Read-only, Searchable, Filterable, Sortable, Show in list (booleans).

**Validation tab** (varies by data type)

| Data type | Fields |
| --- | --- |
| text | minLength, maxLength, pattern |
| number/currency | min, max, precision |
| date/datetime | minDate, maxDate, allowFutureDate, allowPastDate |
| file/image | maxFileSizeMb, allowedExtensions |

**Options tab** — shown **only** for `select`, `multi_select`, `radio`, `checkbox_group`.
Enter: `Low`, `Normal`, `High`, `Urgent` with colors/icons, order, active.

**Visibility tab** — build rules: `other_field <operator> value`. Test **every operator**: `equals`, `not_equals`, `contains`, `is_empty`, `is_not_empty`, `greater_than`, `less_than`.

### 5.5 Configuration → Record Types

| Tab | Field | Type | Input | Condition |
| --- | --- | --- | --- | --- |
| General | Name | text | `Invoice` | required |
| General | Code | text | `invoice` | required, unique, `[a-z0-9_]` |
| General | Description | textarea | `Vendor invoices` | — |
| General | Icon | icon | `i-lucide-receipt` | — |
| General | Color | color | `#14b8a6` | — |
| General | Status | select | Active | — |
| Features | allowAttachments/Comments/Assignment/Sharing/RelatedRecords | boolean | on/off | toggling changes the record UI |
| Features | enableWorkflow | boolean | on | **Workflow tab shown only when on** |
| Features | enableDueDate/History/Export | boolean | on | show/hide due date, history, export |
| Attributes | Assign attributes | builder | `amount`, `due_date`, `approval` | — |
| Card Fields | Card layout | builder | choose slots | only meaningful if the type has a card surface |
| Workflow | Stages + transitions | builder | `Created → Review → Approval → Completed` | only when enableWorkflow |

### 5.6 Organization pages

**Departments** (`/organizations/departments`)

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| Ancestor | select | `Executive Office` | optional; options from `/departments/options?hierarchy=true` |
| Name | text | `Administration` | required |
| Tax ID | text | `K001-123456` | — |
| Email | text | `adm@example.com` | — |
| Phone | text | `+855 23 111 111` | — |
| Description | textarea | `Central administration` | — |
| Address | textarea | `#12, Phnom Penh` | — |
| Contact info | textarea | `Mon–Fri 08:00–17:00` | — |
| Logo | image | `logo-national.svg` | — |
| Is active | boolean | on | — |

**Companies / Purposes / Sectors** — same core fields; Companies add `Sector` + `Purpose` selects; Sectors add `Parent`.

**Officers** (`/officers`)

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| Name | text | `Chan Vanna` | required |
| Organization | select | `Finance` (department) | required |
| Role | select | `Manager` | required; drives permissions |
| Is active | boolean | on | — |
| Authentication enabled | derived badge | — | shown when the officer is linked to a user |

### 5.7 User Management

**Roles** (`/user-management/roles`)

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| Name | text | `Manager` | required |
| Status | select | Active | — |
| Description | textarea | `Department manager` | — |
| Permission matrix (`permissionRows`) | matrix | grant per document type/action | View required for any action; per-row "creator only" toggle and level |

**Users** (`/user-management/users`)

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| Name | text | `Chan Vanna` | required |
| Email | text | `vanna@example.com` | required, unique |
| Role | select | `Manager` | required |
| Officer | select | `Chan Vanna` | optional link |
| Password | password | `Vanna@12345` | required on create; min length |
| Status | select | Active | — |

### 5.8 Record workspaces (dynamic + meetings + documents)

**Meeting Topic** (`/meetings/topics` — kanban/table)

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| Title | text | `Monthly coordination` | required |
| Description | textarea | `Cross-department monthly sync` | — |
| Record time | datetime | `2026-02-10 09:00` | required |
| Tags | csv-list | `monthly, internal` | — |
| Attached meetings | board | `MTG-2026-001`, `MTG-2026-002` | shown after child meetings exist |

**Meeting** (`/meetings/history`, created from a topic → New Meeting)

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| Topic | select | `Monthly coordination` | optional; hidden when created from a topic |
| Letter number | text | `MTG-2026-002` | required |
| Title | text | `Monthly coordination — February` | required |
| Letter date | date | `2026-02-05` | required |
| Meeting date/time | datetime | `2026-02-10 09:00` | required |
| Duration (min) | number | `90` | — |
| Meeting mode | select | `in_person` / `online` / `hybrid` | required |
| Meeting URL | url | `https://zoom.us/j/123` | **most relevant when mode = online/hybrid** |
| Location | text | `Meeting room A` | **most relevant when mode = in_person/hybrid** |
| Participants | multiselect (officers) | Sok Dara, Chan Vanna | — |
| Internal units | multiselect (departments) | Administration, Finance | — |
| External units | multiselect (companies) | Acme Co., Ltd | — |
| Tags | csv-list | `monthly, budget` | — |
| Notes | rich text | meeting minutes | notes dialog |

**Incoming / Outgoing / Document** forms

| Field | Type | Input (Incoming) | Condition |
| --- | --- | --- | --- |
| Title | text | `Purchase request from Acme` | required |
| Document type | select (company) | `Acme Co., Ltd` | required |
| Letter number | text | `INC-2026-000123` | required |
| Letter subject | text | `Purchase request` | required |
| Date | date | `2026-03-01` (received/sent/document) | required |
| Director General date | date | `2026-03-05` | optional |
| Director date | date | `2026-03-04` | optional |
| Involved office | multiselect (departments) | Finance, Procurement | `colSpan 2` |
| Involved officers | multiselect (officers) | Chan Vanna | `colSpan 2` |
| External units | multiselect (companies) | Acme Co., Ltd | `colSpan 2` |
| Tags | csv-list | `purchase, urgent` | `colSpan 2` |

**Master List Request**

| Field | Type | Input |
| --- | --- | --- |
| Title | text | `Update supplier master list` |
| Record time | datetime | `2026-03-20 10:00` |
| Tags | csv-list | `master-list` |

**Dynamic attributes** on a record — every attribute from Step 6 renders by its data type (text, textarea, rich text, number, decimal, currency, boolean, date, time, datetime, email, phone, url, select, multi-select, radio, checkbox group, file, image, organization, officer, user, record reference). Set each and save.

### 5.9 Portal

**File Upload** (`/portal/file-upload`)

| Control | Input | Condition |
| --- | --- | --- |
| Uploader dropzone | `report-q1.pdf`, `photo-office.png` | shown only when storage is ready |
| Storage strip | `Storing on MinIO` | shown when ready |
| Not-configured warning + Open storage settings | — | shown when storage not ready (uploader hidden) |
| Status filter | Active/Disabled | toolbar |
| Created-at range | `2026-02-01 … 2026-03-31` | toolbar |
| Search | `report` | toolbar |
| Page size | 20 | footer |

**Google Drive Sync** (`/portal/google-drive-sync`)

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| Name | text | `Official documents` | when Drive configured |
| Folder name | text | `Official documents` | — |
| Status | select | Active | — |
| Files synced | number | read-only | after sync |
| Error message | textarea | read-only | shown on failure |
| Blocked warning + Open storage settings | — | — | shown when Drive not configured (workspace hidden) |

### 5.10 Export dialog (from any list)

| Field | Type | Input | Condition |
| --- | --- | --- | --- |
| File format | select | `CSV (.csv)` then `Excel (.xlsx)` | always |
| Start date | date | `2026-01-01` | always |
| End date | date | `2026-03-31` | always |
| Scope | select | All matching / Current page / Selected rows | "Selected rows" disabled when nothing selected |
| Fields to include | checkboxes | toggle each; uncheck all → error | always when the list has fields |

### 5.11 List toolbars, comments, attachments

| Control | Input | Condition |
| --- | --- | --- |
| Search box | a keyword | every list |
| Filters | active/inactive, date range, type-specific | per list |
| View switch | Table / Kanban / Timeline / Hierarchy | per entity `views` |
| Sort | e.g. `-meetingDate` | per list |
| Page size / pagination | `20`, page 2 | footer |
| Comments panel | comment text | shown when `allowComments` |
| Attachments panel | upload/detach file | shown when `allowAttachments` |
| Row actions | Detail / Logs / Delete | Delete hidden without permission |

### 5.12 Conditional field scenarios (test each branch)

| # | Scenario | Setup | Expected |
| --- | --- | --- | --- |
| C1 | Attribute options tab | Data type = `select` vs `short_text` | Options tab shown only for select-like types |
| C2 | Visibility rule `equals` | Rule `priority = Urgent` on `urgent_reason` | Field appears only when priority is Urgent |
| C3 | Visibility rule `not_equals` | Rule `priority != Low` | Field hidden when priority = Low |
| C4 | Visibility rule `is_empty` / `is_not_empty` | Rule on `summary` | Toggles with summary content |
| C5 | Visibility rule `greater_than` | Rule `quantity > 10` | Appears above threshold |
| C6 | Workflow off | Record type `enableWorkflow = off` | Workflow tab hidden; no stage column/board |
| C7 | Attachments off | `allowAttachments = off` | Attach action/panel hidden |
| C8 | Comments off | `allowComments = off` | Comments panel hidden |
| C9 | Export off | `enableExport = off` or App Config export disabled | Export disabled/hidden; API returns 403 |
| C10 | Meeting mode online | Set mode = `online` | Meeting URL field relevant; location optional |
| C11 | Meeting mode in-person | Set mode = `in_person` | Location relevant; URL optional |
| C12 | Storage configured | Provider active vs none | Uploader shown vs blocked warning |
| C13 | Drive configured | Provider active vs none | Sync workspace vs blocked warning |
| C14 | No selected rows | Open export with nothing selected | "Selected rows" option disabled |
| C15 | All fields unchecked in export | Uncheck all | "Select at least one field" error, confirm disabled |
| C16 | Selected row gone | Select rows, then change filter | Scope falls back to All matching |
| C17 | Role without permission | Login as Viewer | Page blocked; menus hidden |
| C18 | Record type inactive | Set a type status = Disabled | Type disappears from menus/surfaces |
| C19 | Officer without user | Create officer, no login | No auth; cannot log in |
| C20 | User without officer | Create user, no officer | Can log in; officer fields empty |

---

## 6. Test cases

| ID | Title | Steps | Expected |
| --- | --- | --- | --- |
| T-ENV-01 | Readiness | `GET /ready` | `200`, DB/Redis/broker OK |
| T-AUTH-01 | First-run setup | Fresh DB → open `/auth/login` | Form shows **Create administrator** (name, email, password, confirm) |
| T-AUTH-02 | Registration closes | After setup, `POST /auth/register` again | `403 Registration is closed` |
| T-AUTH-03 | Login | Logout → login with admin / wrong password | Success lands on Dashboard; wrong shows "Invalid email or password" |
| T-AUTH-04 | Rate limit | 11 bad logins in a minute | `429` with cooldown message |
| T-AUTH-05 | Password reset | Forgot password → code (dev shows `debugCode`) → reset → login | New password works; old fails |
| T-AUTH-06 | Session | Refresh page; wait past timeout; refresh token | Session persists; expired session routes to login |
| T-RBAC-01 | Restriction | Login as Viewer → open User Management | Page blocked with permission alert |
| T-RBAC-02 | Record scope | Viewer opens Records | Read-only (no create/edit buttons) |
| T-CFG-01 | Attribute CRUD | Create/edit/delete `priority` | Appears in Attribute Catalog; options available on forms |
| T-CFG-02 | Record type CRUD | Create `document` type with attributes + stages | New menu/route appears; form shows assigned fields; board columns = stages |
| T-ORG-01 | Department tree | Create child under parent | Tree shows hierarchy; self-parent rejected |
| T-ORG-02 | Company/City/Sector/Purpose CRUD | Create + list | Rows appear; referenced selects include them |
| T-OFF-01 | Officer link | Create officer, link user | Officer user resolves names; no raw UUIDs in lists |
| T-USER-01 | Create user | Create user with Manager role | Can log in with granted permissions |
| T-REC-01 | Create record | New Incoming Document, fill title/priority/due date | Saved with generated number/record time |
| T-REC-02 | Stage transition | Drag/move a record to next stage | Stage updates; log entry recorded |
| T-REC-03 | Concurrency | Open same record in two tabs, save both | Second save rejected with conflict (version/If-Match) |
| T-REC-04 | Archive/Restore | Archive then restore | Leaves active list; returns on restore |
| T-REC-05 | Comments/attachments | Add comment + attach file (if enabled) | Visible in activity/attachments |
| T-MEET-01 | Topic + meeting | Create topic, create meeting assigned to topic | Topic shows child meetings; timeline shows meeting |
| T-MEET-02 | Meeting attendees | Set participants/internal/external units | Card shows participant count and names |
| T-PORTAL-01 | Upload | Upload pdf/png/csv | Stored on MinIO; download from `/api/v2/files/{id}` works |
| T-PORTAL-02 | Storage guard | With no provider and env S3 empty, open File Upload | Uploader hidden, warning + "Open storage settings" shown |
| T-PORTAL-03 | Drive guard | With no Drive provider, open Google Drive Sync | Workspace blocked with warning + settings link |
| T-PORTAL-04 | Drive sync | Configure Drive, create source, run sync | Job queued → completed; files listed |
| T-STORAGE-01 | S3 test | App Config → Amazon S3 → Test connection | `Connected to <bucket>` or clear failure |
| T-SEARCH-01 | Search | Search record + officer | Matching results with correct entity types |
| T-DASH-01 | Dashboard | After data created | Counts/KPIs reflect created records |
| T-LOG-01 | Audit | Open `/records/logs` | Shows create/edit/transition with actor + time |
| T-EXPORT-01 | CSV export | Export list as CSV with date range + fields | Download opens in Excel with Khmer text intact |
| T-EXPORT-02 | Excel export | Export as Excel (.xlsx) | Header row + data; template columns matched by label, others blank |
| T-EXPORT-03 | Export disabled | App Config → disable export → Export | `403` / export option unavailable |
| T-I18N-01 | Locale switch | Switch KM then EN | Sidebar, forms, dialogs translate; date/number format follows locale |
| T-I18N-02 | Record type labels | Switch KM | Built-in types show Khmer labels; custom types keep configured name |
| T-NOTIF-01 | Email (if SMTP set) | Test email from App Config | Test email delivered |
| T-NOTIF-02 | Telegram (if set) | Test Telegram connection/message | Message received in the configured chat |
| T-SEC-01 | Security headers | Inspect response headers | CSP, X-Content-Type-Options, X-Frame-Options present |
| T-SEC-02 | CSRF | Send a POST without `X-CSRF-Token` | `403` |

---

## 7. Edge cases & notes

- **No users yet** → setup form; **registry closed** after the first user.
- **Storage not configured** → portal upload is blocked with a warning; the API falls back to env `S3_*`.
- **Google Drive not configured** → Drive Sync page is blocked.
- **Built-in record types are not auto-seeded** — create types with the exact built-in codes to get the correct surface/menu.
- **Excel templates** live in `backend/app/resources/export_templates/<resource>.xlsx` (e.g. `documents.xlsx`); without a template, a plain sheet is generated. Header labels must match the export field labels (or the field code) used at export time.
- **Concurrency**: keep the `version` field current (`If-Match`) or the save returns a conflict.
- **Locale**: every new user-facing string needs both `en` and `km` keys.
- **Data safety**: do not run destructive tests against production; use a scratch DB/volume.
