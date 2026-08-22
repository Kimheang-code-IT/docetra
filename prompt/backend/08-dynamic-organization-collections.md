# Dynamic organization collections

Canonical contract for Docetra’s unified organization surface (department + company). Prefer this document over older static path lists when they conflict.

## Principle

**Department** and **company** are one `organization` table differentiated by type. The API and UI must not treat them as unrelated product domains. Sector, purpose, and officer remain sibling master-data lookups that feed organization forms and record pickers.

## API path shape

Use:

```text
/api/v2/organizations/{orgType}
/api/v2/organizations/{orgType}/{id}
/api/v2/organizations/{orgType}/options
/api/v2/organizations/_meta/types
```

`orgType` is closed:

| API `orgType` | DB `organization.organization_type` |
| --- | --- |
| `department` | `government` |
| `company` | `company` |

Reject unknown `orgType` with `404`.

Reserved path segments under `/organizations/` (not org types): `_meta`, `sectors`, `purposes`, `officers`.

Do **not** mount department or company as bare `/api/v2/{orgType}/…`. Sector, purpose, and officer are not org types; they use top-level collections below.

### Standard collection surface (`department` | `company`)

Same behavior as the shared entity router:

- `GET/POST` collection; `GET/PATCH/DELETE` item
- `POST …/archive`, `…/restore`, `…/bulk-delete`
- `DELETE …/purge`
- `GET …/counts`, `…/options`
- `GET/POST …/comments`, `GET …/activity`, `…/attachments`, `…/neighbors`, `…/favorite`

Plus:

- `GET /api/v2/organizations/_meta/types` — descriptors for FE boot (icons, route bases, which rules apply)

### Lookup siblings (not `{orgType}`)

Canonical collections (same shared entity router as other master data):

```text
/api/v2/sector
/api/v2/purpose
/api/v2/officers
```

Do not also expose nested `/organizations/sectors|purposes|officers` paths.

There is **one** sectors collection and **one** purposes collection — do not also expose `/company-sectors` or `/company-purposes` as separate APIs.

There are **no** plural HTTP aliases (`/organizations/departments`, `/organizations/companies`). UI may still use plural page routes; the API always uses `orgType` (`department`, `company`).

## Type-specific rules

### Company

- Create/update **persist** `sectorId` and `purposeId` / `organizationPurposeId` when provided.
- Validate FKs exist and are active; unknown ids → `422`.
- Sector/purpose are classification only (not hierarchy).
- Do not require department-style parent trees for companies (parent may remain unused).

### Department

- Hierarchy only: optional `parentId` pointing at another **department** (same `organization_type`).
- Reject self-parent, cross-type parent, and cycles.
- Set `lvl` from parent (`1` at root, `parent.lvl + 1` otherwise).
- List supports `parentId` and `rootsOnly=true` for tree UIs.
- `/options?hierarchy=true` returns `parentId` for nested selects.

### Officer

- Belongs to one organization (`organizationId` / `departmentId`).
- Exposed for record pickers via `/api/v2/officers/options`.
- Not an `{orgType}` value.

## Record reuse

Document and meeting records reuse organization and officer options:

- Departments: `/api/v2/organizations/department/options`
- Companies: `/api/v2/organizations/company/options`
- Officers: `/api/v2/officers/options`

Prefer storing **UUIDs** in record detail fields (`officeInCharge`, `internalUnits`, `externalUnits`, `involvedOfficers`, `participants`, …). Accept legacy name strings on read during migration.

On record create/update, sync `record_organization` rows from known org-bearing detail fields (role_type such as `owner` / `participant`). Officers stay on officer fields — do not invent org rows for people.

## Permissions

Keep existing prefixes mapped from orgType:

- `department` → `organizations.departments.*`
- `company` → `organizations.companies.*`
- sectors → `organizations.sectors.*`
- purposes → `organizations.purposes.*`
- officers → `organizations.officers.*`

## Frontend shells

- Boot: `GET /organizations/_meta/types`.
- Routes: `/organizations/departments`, `/organizations/companies` (or `/organizations/[orgType]`).
- Adapter: `createOrganizationAdapter(orgType)` → `/api/v2/organizations/${orgType}`.
- Company form: sector + purpose selects from lookup `/options`.
- Department form: parent select with hierarchy.
- Record forms: org/officer attribute types use the options endpoints above (`valueField=id`).

## Related

- [`modules/organization-master-data.md`](./modules/organization-master-data.md)
- [`07-dynamic-record-collections.md`](./07-dynamic-record-collections.md)
- [`00-integration-contract.md`](./00-integration-contract.md)
- [`../frontend/00C-dynamic-record-fields.md`](../frontend/00C-dynamic-record-fields.md)
