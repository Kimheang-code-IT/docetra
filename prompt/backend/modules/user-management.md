# User Management — Roles & Users (Backend Logic)

> **UI scope:** User Management nav — **Role**, **User**; officers live under Organization but share access model.  
> **References:** `prompt/specification/modules/people-access.md`, `prompt/specification/04-permissions-and-access.md`, `frontend/app/utils/role/permissions.ts`.

---

## 1. Purpose

User Management configures **who can sign in** and **what they can do**:

| Route | UI | Flow |
| --- | --- | --- |
| `/user-management/roles` | `EntityWorkspaceView` + table | List roles; create/edit role document |
| `/user-management/roles/new`, `/:id` | `EntityDocumentView` | Permission matrix per document/record type |
| `/user-management/users` | `EntityWorkspaceView` | List users |
| `/user-management/users/new`, `/:id` | `EntityDocumentView` | Account + link to officer, assign roles |

**Auth** (login, reset password) is separate under `/auth/*` but uses the same user store.

Backend is **source of truth** for authorization; UI only hides actions.

---

## 2. Domain entities

### Role

| Field | Role |
| --- | --- |
| `id`, `name`, `code` | Identity |
| `status` | active / disabled |
| `permissions` | Flat permission keys **or** structured matrix |
| `permissionRows` | UI matrix: entity × actions (frontend saves → flat keys) |

Frontend converts matrix to flat keys via `permissionRowsToFlatKeys` on save.

### User (account)

| Field | Role |
| --- | --- |
| `id`, `email`, `name` | Login identity |
| `status` | active / disabled / locked |
| `roleIds` or embedded roles | Assigned roles |
| `officerId` | Optional link to Organization officer |
| `avatar` | Optional URL |
| Secrets | Password hash only server-side; never in GET |

### Officer (organization module)

- Business person; optional `userId` back-link.
- User Management **references** officer; officer CRUD stays under `/api/v2/organizations/officers`.

---

## 3. Permission model

Permissions are **string codes** aligned with frontend `definePageMeta.permission` and entity configs, e.g.:

- `records.incoming_documents.view`
- `meetings.topics.view`
- `portal.file_upload.view`
- `configuration.record_types.edit`
- `settings.app_config.view`

### Evaluation flow

```text
Request → authenticate JWT/session
       → load user + roles
       → expand role permissions (union)
       → check required code for route/action
       → optional org/department scope filter on data queries
```

Menu visibility may use same codes; denying menu does not replace API checks.

### Role document matrix

The UI edits **document-type × action** rows (`AppRolePermissionMatrix`). Backend should either:

- Store matrix JSON and expand at login, or
- Store expanded flat list on save (current frontend sends flat `permissions` on payload)

Keep one canonical form in DB to avoid drift.

---

## 4. API surface (proposed)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v2/users/roles` | List roles |
| GET | `/api/v2/users/roles/{id}` | Role detail |
| POST | `/api/v2/users/roles` | Create |
| PATCH | `/api/v2/users/roles/{id}` | Update permissions |
| DELETE | `/api/v2/users/roles/{id}` | Disable/delete |
| GET | `/api/v2/users` | List users |
| GET | `/api/v2/users/{id}` | User detail |
| POST | `/api/v2/users` | Create (invite/set password flow TBD) |
| PATCH | `/api/v2/users/{id}` | Update roles, status, officer link |
| POST | `/api/v2/auth/login` | Issue token (see auth adapter) |

List endpoints: pagination, search on name/email/code, sort.

---

## 5. User flows

### Create role

1. Admin opens `/user-management/roles/new`.
2. Enters name/code; configures permission matrix.
3. Save → `POST /roles` → redirect to `/:id`.
4. Activity: `role.created`.

### Edit role permissions

1. Change matrix → save → `PATCH`.
2. Existing sessions: policy choice — re-load permissions on next request or force refresh token.

### Create user

1. Admin opens `/user-management/users/new`.
2. Email, name, roles, optional officer.
3. Save → backend creates user + sends set-password email (future) or temp password policy.

### Disable user

- `status=disabled` → login rejected; active tokens revoked.

---

## 6. Security rules

| Rule | Detail |
| --- | --- |
| Password storage | Strong hash (argon2/bcrypt); never log |
| Rate limit | Login and forgot-password endpoints |
| Self-edit | Users may not grant themselves super-admin unless break-glass policy |
| Last admin | Prevent delete/disable last role with `settings.*.edit` |
| Audit | Security-sensitive changes → system log + activity |

---

## 7. Permissions (meta)

| Code | Use |
| --- | --- |
| `users.roles.view` / `.edit` | Role pages |
| `users.users.view` / `.edit` | User pages |

Exact strings match `entityConfigs.roles.permission` and `users.permission` in frontend.

---

## 8. Frontend contract

| Concern | Code |
| --- | --- |
| Entities | `config/entities.ts` → `roles`, `users` |
| Matrix | `AppRolePermissionMatrix.vue`, `utils/role/permissions.ts` |
| Adapter | `adapters/index.ts` → `ROLES`, `USERS` |
| Auth | `adapters/auth.ts`, `stores/auth.ts`, `middleware/auth.global.ts` |
| Endpoints | `api-endpoints.ts` |

Document pages use shared comments/activity when enabled on entity config.

---

## 9. Validation

| Case | Result |
| --- | --- |
| Duplicate role code | 409 |
| Invalid permission key | 422 |
| User email duplicate | 409 |
| Officer already linked to another user | 422 |
| Delete role assigned to users | 409 with count |

---

*Officer hierarchy and department scope are extended in Organization module; User Management consumes officer id only.*
