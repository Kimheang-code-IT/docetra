# Organization — Departments, Companies & Officers (Backend Logic)

> **UI scope:** Organization nav — **Department**, **Company**, **Company Purpose**, **Company Sector**, **Officer**.  
> **References:** `prompt/specification/modules/organization.md`, `prompt/specification/modules/people-access.md` (officer ↔ user), `frontend/app/config/entities.ts` (`departments` … `officers`).

---

## 1. Purpose

Organization is the **master-data** layer for administrative structure:

| Route | UI | Backend role |
| --- | --- | --- |
| `/organizations/departments` | `EntityWorkspaceView` table | Internal hierarchy (parent department) |
| `/organizations/companies` | table | External/partner companies + sector/purpose |
| `/organizations/company-purposes` | table | Reference list for companies |
| `/organizations/company-sectors` | table | Reference tree for companies |
| `/organizations/officers` | table | People linked to org/department (+ optional user) |
| `/*/new`, `/*/:id` | `EntityDocumentView` | Create / detail / edit |

These entities are **not** workflow records. They feed:

- Record ownership, sender/recipient, parties
- Meeting participants / units
- User ↔ officer mapping (User Management)
- Lookup selects (`/options` endpoints)

**Presentation:** server-paginated tables (supports page sizes including **All**), document pages with comments/activity where `canComment` is true, row actions Detail / Logs / Delete.

---

## 2. Domain entities

Unified product idea: organizations share a conceptual `organization` model. Current UI splits into five resources that map cleanly to REST collections (and optionally to one polymorphic table with `type`).

### 2.1 Department

Internal administrative unit with optional parent (ancestor).

| Field | Role |
| --- | --- |
| `id`, `code`, `name` | Identity (`name` required) |
| `parentId`, `parentName` | Hierarchy; denormalized name for lists |
| `isActive` / `status` | Soft enable (`isActive` ↔ `status` active/disabled) |
| `taxId`, contacts, address, logo | Profile |
| `officerCount`, `relatedRecordCount` | Computed / denormalized counters |

**Rules:**

- Cannot set `parentId` to self.
- Hierarchy must be **cycle-safe** (reject if new parent is a descendant).
- Deactivating a department does not auto-delete children; optional policy: block deactivate when children exist.

### 2.2 Company

External or partner organization.

| Field | Role |
| --- | --- |
| `name` | Required |
| `sectorId`, `sectorName` | FK → company sector |
| `purposeId`, `purposeName` | FK → company purpose |
| `taxId`, `registrationNumber` | Identifiers |
| Contacts, address, logo, `isActive` | Profile |
| `relatedRecordCount` | Usage counter |

### 2.3 Company purpose

| Field | Role |
| --- | --- |
| `name` | Required |
| `description`, `isActive` | Optional |
| `usageCount` | How many companies reference it |

Disable rather than hard-delete when `usageCount > 0` (or return 409).

### 2.4 Company sector

| Field | Role |
| --- | --- |
| `name` | Required |
| `parentId`, `parentName` | Optional sector tree |
| `description`, `isActive`, `usageCount` | Same patterns as purpose |

Same cycle and usage rules as departments/purposes.

### 2.5 Officer

Business person (not the login account itself).

| Field | Role |
| --- | --- |
| `name` | Required |
| `email`, `phone`, `code` | Contact / HR id |
| `departmentId` / `organizationId` | Belonging |
| `roleId`, `roleName` | Optional job/system role label |
| `userId` | Optional link to User Management account |
| `authenticationEnabled` | True when `userId` is set (UI derived) |
| `isActive` | Soft enable |

**Identity rules** (from people-access):

- Not every officer needs a user account.
- A user should map to **at most one** officer when linked.
- Access evaluation uses officer’s org/department scope when product requires it.

---

## 3. List & document flows

### List (all five)

```text
GET /api/v2/organizations/{resource}?q=&page=&limit=&sort=&isActive=&startDate=&endDate=
```

| Query | Behavior |
| --- | --- |
| `q` | Search name, code, email, tax id, etc. |
| `page`, `limit` | Server pagination; `limit=all` → large fetch (see frontend pagination utils) |
| `sort` | Default `-updatedAt` |
| `isActive` | Boolean filter |
| Date range | Filter on `updatedAt` (UI date filter) |

List rows should include denormalized names (`parentName`, `sectorName`, …) and `rowNumber` when requested by UI.

### Document create / edit

```text
POST / PATCH /api/v2/organizations/{resource}
GET  /api/v2/organizations/{resource}/{id}
```

After create → client navigates to `/:id`. Comments/activity/attachments use shared sub-resources when enabled.

### Lookup options (select fields)

Used by Organization forms **and** Record Incoming/Outgoing/Document forms:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v2/organizations/departments/options` | Parent department; **Involved office** on records |
| GET | `/api/v2/organizations/companies/options` | **Document type** + **External units** on records |
| GET | `/api/v2/organizations/company-sectors/options` | Active sectors |
| GET | `/api/v2/organizations/company-purposes/options` | Active purposes |
| GET | `/api/v2/organizations/officers/options` | **Involved officers** on records |

**Query:** `valueField=name` → option `value` is the display name (current Record UI stores names on the record). Default / omit → `value` is `id` (preferred for FK storage + denormalized `*Name`).

Options should be **bounded**, searchable, active-only by default, and exclude the current record from parent candidates when editing (cycle safety on client is not enough).

---

## 4. API surface (aligned with frontend)

| Resource | Base path (current) |
| --- | --- |
| Departments | `/api/v2/organizations/departments` |
| Companies | `/api/v2/organizations/companies` |
| Company purposes | `/api/v2/organizations/company-purposes` |
| Company sectors | `/api/v2/organizations/company-sectors` |
| Officers | `/api/v2/organizations/officers` |

Standard CRUD per resource:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `{base}` | List |
| GET | `{base}/{id}` | Detail |
| POST | `{base}` | Create |
| PATCH | `{base}/{id}` | Update |
| DELETE | `{base}/{id}` | Soft-delete / archive |
| POST | `{base}/bulk-delete` | Optional multi-delete |
| GET | `{base}/options` | Lookup |

Shared:

| Method | Path |
| --- | --- |
| GET/POST | `/api/v2/{entityPath}/{id}/comments` |
| GET | `/api/v2/{entityPath}/{id}/activity` |
| GET/POST | `/api/v2/{entityPath}/{id}/attachments` |

---

## 5. Key operations & validations

| Case | Result |
| --- | --- |
| Missing `name` | 422 |
| Duplicate `code` (when used) | 409 |
| Parent = self | 422 |
| Parent creates cycle | 422 |
| Invalid sector/purpose id | 422 / 404 |
| Deactivate sector/purpose still in use | 409 or force-disable with warning |
| Delete department with officers/records | 409 unless cascade policy defined |
| Officer email uniqueness (optional) | 409 |
| Link officer to user already linked | 422 |
| Edit without permission | 403 |

Frontend already guards some cases (e.g. department cannot be own ancestor) — **backend must enforce** the same.

---

## 6. Permissions

| Code | Use |
| --- | --- |
| `organizations.departments.view` / `.edit` | Departments |
| `organizations.companies.view` / `.edit` | Companies |
| `organizations.company_purposes.view` / `.edit` | Purposes |
| `organizations.company_sectors.view` / `.edit` | Sectors |
| `organizations.officers.view` / `.edit` | Officers |

Exact strings match `entityConfigs.*.permission` in the frontend.

---

## 7. Activity & audit

Emit activity on create/update/status change:

- `organization.created` / `organization.updated` (or entity-specific codes)
- `officer.linked_user` / `officer.unlinked_user`
- Hierarchy change: include previous/new `parentId` in redacted metadata

Record **logs** deep-link may open `/records/record-logs` with search on entity id/title when product wires row action **Logs**.

---

## 8. Cross-module relationships

```text
Company Purpose ──┐
Company Sector  ──┼──▶ Company ──▶ Record (party / sender / recipient)
                  │
Department ───────┼──▶ Officer ──▶ User (optional)
                  │
                  └──▶ Record (owner department / office)
```

| Consumer | Uses |
| --- | --- |
| **Record** | Org FKs / names on documents (`documentType`, involved office/officers, external units); lookup options |
| **Meeting** | Units / participants labels |
| **User management** | `officerId` on user; officer may show `userId` |
| **Reporting** | Filters by department/company/sector |

Organization APIs must stay **lookup-friendly** (stable ids, active flags, denormalized labels).

---

## 9. Frontend contract (implemented)

| Concern | Code |
| --- | --- |
| Entity configs | `frontend/app/config/entities.ts` → `departments`, `companies`, `companyPurposes`, `companySectors`, `officers` |
| Types | `frontend/app/types/docetra/entities.ts` |
| List/detail pages | `pages/organizations/**` → `EntityWorkspaceView` / `EntityDocumentView` |
| Adapter | `adapters/index.ts` + `createEntityAdapter` |
| Endpoints | `api-endpoints.ts` → `DEPARTMENTS`, `COMPANIES`, `COMPANY_PURPOSES`, `COMPANY_SECTORS`, `OFFICERS` |
| Parent/options load | `adapters/reference-options.ts`, document page save resolves `parentName` |
| Status sync | `isActive` ↔ `status` in `useDocumentPage` |

**Mock → HTTP:** `NUXT_PUBLIC_USE_MOCK_DATA=false` uses the same paths.

---

## 10. Implementation notes

- Prefer **soft disable** (`isActive=false`) over hard delete for master data.
- Keep hierarchy and sector trees **cycle-safe** in one shared service.
- Options endpoints should be indexed and capped (never return unbounded catalogs).
- Do not embed record workflow logic in this module.
- Counters (`officerCount`, `usageCount`, `relatedRecordCount`) may be maintained async or computed on read.

---

*Align with `prompt/specification/modules/organization.md` for ownership; this file defines the screen-level API contract matching current Nuxt routes.*
