# User Management — Roles & Users (Backend Logic)

> **UI scope:** User Management nav — **Role**, **User**; officers live under Organization but share access model.  
> **References:** `prompt/specification/modules/people-access.md`, `prompt/specification/04-permissions-and-access.md`, `frontend/app/utils/role/permissions.ts`.

---

## 1. Purpose

User Management configures **who can sign in** and **what they can do**:


| Route                                | UI                            | Flow                                       |
| ------------------------------------ | ----------------------------- | ------------------------------------------ |
| `/user-management/roles`             | `EntityWorkspaceView` + table | List roles; create/edit role document      |
| `/user-management/roles/new`, `/:id` | `EntityDocumentView`          | Permission matrix per document/record type |
| `/user-management/users`             | `EntityWorkspaceView`         | List users                                 |
| `/user-management/users/new`, `/:id` | `EntityDocumentView`          | Account + link to officer, assign roles    |


**Auth** (login, forgot/reset password) is separate under `/auth/*` but uses the same user store. Forgot-password delivery uses the third-party email adapter and anti-enumeration contract in `../03-notifications-and-integrations.md`.

Backend is **source of truth** for authorization; UI only hides actions.

The current frontend middleware enforces page metadata and shared components gate action buttons. New routes use `.create`; list/detail routes use `.view`; save, delete, comments, exports, and configuration controls use their corresponding action suffix. Direct API calls must produce the same authorization result even when the UI is bypassed.

---

## 2. Domain entities

### Role


| Field                | Role                                                     |
| -------------------- | -------------------------------------------------------- |
| `id`, `name`, `code` | Identity                                                 |
| `status`             | `active` / `archived` / `deleted`; administrator-managed lifecycle |
| `permissions`        | Flat permission keys **or** structured matrix            |
| `permissionRows`     | UI matrix: entity × actions (frontend saves → flat keys) |


Frontend converts matrix to flat keys via `permissionRowsToFlatKeys` on save.

### User (account)


| Field                       | Role                                         |
| --------------------------- | -------------------------------------------- |
| `id`, `email`, `name`       | Login identity                               |
| `status`                    | `active` / `disabled` / `locked` / `deleted`; self-delete means disabled |
| `roleIds` or embedded roles | Assigned roles                               |
| `officerId`                 | Optional link to Organization officer        |
| `avatar`                    | Optional URL                                 |
| Secrets                     | Password hash only server-side; never in GET |


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
Request → authenticate server-side cookie session
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

The implemented frontend contract uses canonical actions: `view`, `create`, `edit`, `archive`, `restore`, `delete`, `purge`, `assign`, `share`, `export`, `comment`, `transition`, and `configure`. Every matrix document type declares a permission namespace matching route metadata, for example `incoming_document` expands to `records.incoming_documents.*` and `role` expands to `users.roles.*`. `purge` is administrator-only and cannot use creator-only scope.

The permission catalog covers every protected frontend area: Meetings, all Record workspaces and logs, Organization master data, Users/Roles, Record Type/Attribute configuration, uploads and Drive sync, Portal/System logs, App Config, App Info, and Storage. Each catalog item declares its allowed action subset; the API rejects actions that are not applicable to that item. Published dynamic Record Types are appended by `/permission-catalog` using stable type IDs/codes and must not require a frontend release.

Permission dependency rules are deterministic:

- Granting any action automatically grants `view`.
- Removing `view` removes every dependent action in that row.
- `onlyIfCreator` is valid only when at least one action is granted.
- `level` is an integer from `0` through `9` and is scope metadata, not a permission string.
- Unknown document types or actions are rejected by the API; the frontend drops legacy/unknown values while normalizing responses.
- Legacy UI actions are migrated as follows: `select|read|report|mask → view`, `write → edit`, `email → comment`, and `import → create`.

Create and update send both the structured source and an expanded, sorted capability list:

```json
{
  "name": "Records Officer",
  "code": "RECORDS_OFFICER",
  "status": "active",
  "permissionSchemaVersion": 1,
  "permissionRows": [
    {
      "id": "perm_incoming_document",
      "documentType": "incoming_document",
      "actions": ["view", "create", "edit", "export"],
      "onlyIfCreator": false,
      "level": 0
    }
  ],
  "permissions": [
    "records.incoming_documents.create",
    "records.incoming_documents.edit",
    "records.incoming_documents.export",
    "records.incoming_documents.view"
  ],
  "permissionCount": 4
}
```

The backend must treat `permissionRows` as the canonical write model, recompute `permissions` and `permissionCount`, and reject a mismatch with `422 permission_payload_mismatch`. Never trust client-expanded keys without recomputation.

---

## 4. API surface (proposed)


| Method | Path                               | Purpose                                                                               |
| ------ | ---------------------------------- | ------------------------------------------------------------------------------------- |
| GET    | `/api/v2/users/roles`              | List roles                                                                            |
| GET    | `/api/v2/users/roles/{id}`         | Role detail                                                                           |
| POST   | `/api/v2/users/roles`              | Create                                                                                |
| PATCH  | `/api/v2/users/roles/{id}`         | Update permissions                                                                    |
| GET    | `/api/v2/users/permission-catalog` | Permission-filtered document/action catalog, including published dynamic Record Types |
| DELETE | `/api/v2/users/roles/{id}`         | Disable/delete                                                                        |
| GET    | `/api/v2/users`                    | List users                                                                            |
| GET    | `/api/v2/users/{id}`               | User detail                                                                           |
| POST   | `/api/v2/users`                    | Create (invite/set password flow TBD)                                                 |
| PATCH  | `/api/v2/users/{id}`               | Update roles, status, officer link                                                    |
| POST   | `/api/v2/auth/login`               | Create session cookie and return safe user profile                                    |
| GET    | `/api/v2/auth/me`                  | Validate session and return user plus `pageAccess`                                    |
| POST   | `/api/v2/auth/logout`              | Revoke session and clear auth/CSRF cookies                                            |
| POST   | `/api/v2/auth/forgot-password`     | Uniform accepted response; enqueue reset email when eligible                          |
| POST   | `/api/v2/auth/reset-password`      | Consume one-time reset token, change password, revoke sessions                        |


List endpoints: pagination, search on name/email/code, sort.

Mutation responses return the normalized `permissionRows`, recomputed `permissions`, `permissionCount`, `permissionSchemaVersion`, and normal entity timestamps. Permission changes produce an immutable activity event containing added/removed capability codes but no sensitive record data. Return `409 role_version_conflict` when optimistic versioning detects a stale role update.

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

- Self-service account deletion and administrator disable set `status=disabled`; login is rejected and all sessions/reset tokens are revoked. Only an authorized administrator can reactivate.
- Administrator soft delete sets `status=deleted`; administrator restore is allowed. Purge/anonymization follows retention rules and preserves a content-free audit actor reference.
- Role archive/restore/delete/purge is administrator-only; an assigned role and the last security-administrator role cannot be purged.

---

## 6. Security rules


| Rule             | Detail                                                                                  |
| ---------------- | --------------------------------------------------------------------------------------- |
| Password storage | Strong hash (argon2/bcrypt); never log                                                  |
| Rate limit       | Login and forgot-password endpoints                                                     |
| Browser session  | Secure + HttpOnly + SameSite cookie; rotate session IDs and revoke on logout/disable    |
| CSRF             | Require same-origin validation and `X-CSRF-Token` for cookie-authenticated mutations    |
| Token exposure   | Never return refresh/session secrets in user JSON, logs, query strings, or localStorage |
| Self-edit        | Users may not grant themselves super-admin unless break-glass policy                    |
| Last admin       | Prevent delete/disable last role with `settings.*.edit`                                 |
| Audit            | Security-sensitive changes → system log + activity                                      |


---

## 7. Permissions (meta)


| Code                                                                | Use                              |
| ------------------------------------------------------------------- | -------------------------------- |
| `users.roles.view` / `.create` / `.edit` / `.delete` / `.configure` | Role pages and permission matrix |
| `users.users.view` / `.create` / `.edit` / `.delete` / `.configure` | User pages                       |


Exact strings match `entityConfigs.roles.permission` and `users.permission` in frontend.

---

## 8. Frontend contract


| Concern   | Code                                                              |
| --------- | ----------------------------------------------------------------- |
| Entities  | `config/entities.ts` → `roles`, `users`                           |
| Matrix    | `AppRolePermissionMatrix.vue`, `utils/role/permissions.ts`        |
| Adapter   | `adapters/index.ts` → `ROLES`, `USERS`                            |
| Auth      | `adapters/auth.ts`, `stores/auth.ts`, `middleware/auth.global.ts` |
| Endpoints | `api-endpoints.ts`                                                |


Document pages use shared comments/activity when enabled on entity config.

---

## 9. Validation


| Case                                                      | Result                                                               |
| --------------------------------------------------------- | -------------------------------------------------------------------- |
| Duplicate role code                                       | 409                                                                  |
| Invalid permission key                                    | 422                                                                  |
| Action without required `view` after server normalization | Normalize or 422 according to API policy; response must be canonical |
| Invalid creator scope or level outside 0–9                | 422                                                                  |
| Client flat keys differ from server expansion             | 422 `permission_payload_mismatch`                                    |
| Stale permission schema/version                           | 409 `role_version_conflict`                                          |
| User email duplicate                                      | 409                                                                  |
| Officer already linked to another user                    | 422                                                                  |
| Delete role assigned to users                             | 409 with count                                                       |


---

*Officer hierarchy and department scope are extended in Organization module; User Management consumes officer id only.*
