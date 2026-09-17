# Docetra — Organization (Departments, Companies, Sectors, Purposes, Officers)

Verified implementation: `modules/organization/*` (backend), `config/entities.ts` departments/companies/purposes/sectors/officers, pages `/organizations/*`, `/purpose`, `/sector`, `/officers`.

## Data model

```
organization (organization_type = department | company)
  ├── parent_id → organization        (main department → sub-departments; company groups)
  ├── sector_id → organization_sector (sector may have parent_id → sub-sectors)
  ├── organization_purpose_id → organization_purpose
  ├── child_ids, lvl                  (denormalized hierarchy helpers)
  └── 1─n officer

officer
  ├── organization_id → organization
  ├── role_id → role                  (business role label)
  ├── auth_id → users (nullable)      (optional login account)
  └── 1─n officer_identifier          (typed identifiers)
```

## Departments

- Fields: name (required), parent (select), taxId, contactEmail/Phone, contactInfo, address, description, logo (image URL), isActive.
- Main vs sub-department is pure hierarchy (`parentId`); `lvl`/`child_ids` maintained by the service.
- Cycle-safe: reparenting that creates a loop is rejected.
- Usage: selectable via department @mention (`internalUnits`) on meetings and documents; record type × organization permissions (`record_type_permission`).

## Companies

- Fields: name (required), taxId, **sectorId** (select), **purposeId** (select), contacts, address, description, logo, isActive.
- Sector and Purpose are **reusable catalogs** (`/sector`, `/purpose` pages) — company forms select from them; both support activate/deactivate.
- Usage: `externalUnits` @mention on meetings/documents; `senderOrganization`/`recipientOrganization` on documents.

## Sectors

- Name (required), parent (sub-sector), description, isActive. Flat list display shows parentName.

## Purposes

- Name (required), description, isActive.

## Officers

- Fields: name (required), organizationId, roleId, email, identifiers, profile URL (avatar), isActive, authenticationEnabled (derived from `auth_id` presence).
- Officers are the **reusable assignment pool** for meetings and documents: `participants`, `involvedOfficers`, owner/assignee.
- Not every officer has a user account; user management maps users → officers.

## API (same family for each resource)

`GET list` (`q,page,limit,sort,status,isActive`) · `counts` · `options` · `GET /{id}` (+ activity/comments/attachments/neighbors) · `POST` · `PUT /{id}` (If-Match) · `PATCH /{id}/stage` · `POST archive|restore|bulk-delete` · `DELETE /{id}` · `DELETE /{id}/purge`.

Organizations use `/organizations/{org_type}` with `department|company` (registry: `GET /organizations/_meta/types`). Purposes: `/purpose`; sectors: `/sector`; officers: `/officers`.

## Permissions

| Resource | Actions |
|---|---|
| organizations.departments / companies | MASTER: view, create, edit, delete, export, comment |
| organizations.purposes / sectors / officers | MASTER |
| archive restore for orgs | via resource archive/restore actions |

## Business rules

- Name required; type must be valid; references (sector/purpose/parent) must exist and be active.
- Status changes validated; active flag gates select options.
- All changes preserve history (audit + activity).
- Deleting an organization with officers/records attached is guarded (FK integrity; soft delete preferred).
