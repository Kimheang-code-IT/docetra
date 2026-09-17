# Docetra — RBAC (Roles, Permissions, Access)

## Model

- **User** (`users`) authenticates; optionally maps 1:1 to an **Officer** (`users.officer_id` ↔ `officer.auth_id`). Officers can exist without accounts.
- **Role** (`role`) groups **Permission** rows (`permission`: `role_id`, `code`, `is_enable`, `scope`).
- **Permission code** = `{resource_prefix}.{action}`.
- **`scope`**: `all` (normal) | `creator` (only resources the user created). This is the canonical `onlyIfCreator` mechanism (migration 0010 `permission.scope`).

## Action sets (`core/permissions.py`)

| Set | Actions | Applies to |
|---|---|---|
| WORKFLOW | view, create, edit, archive, restore, delete, purge, assign, share, export, comment, transition | Record types |
| MASTER | view, create, edit, delete, export, comment | organizations, purposes, sectors, officers |
| USERS | view, create, edit, archive, restore, delete, purge, comment, configure | users, roles |
| CONFIG | view, create, edit, delete, export, comment, configure | record types, record attributes |
| AUDIT | view, export | record logs, portal logs, system logs |
| SETTINGS | view, edit, configure | app info, app config, storage |
| Portal | view, create, delete, share, export | file uploads |
| Portal config | view, create, edit, delete, export, comment | google drive sync |
| Fixed | view | dashboard, archive |

### Resource prefixes

Record types (from `permission_prefix_for_type_code`): `records.meeting_topic`, `records.meeting_history`, `records.incoming_documents`, `records.outgoing_documents`, `records.documents`, `records.master_list_requests`, dynamic `records.{type_code}` for admin-created types.

Static: `dashboard`, `archive`, `organizations.departments|companies|purposes|sectors|officers`, `users.users`, `users.roles`, `configuration.record_types|record_attributes`, `records.logs`, `portal.file_upload`, `portal.google_drive_sync`, `portal.logs`, `system.logs`, `settings.app_config|app_info|storage`.

The catalog is rebuilt when Record seeds new types (`configure_record_permissions` → `refresh_permission_tables`), so **new record types get permission rows automatically** — no frontend hardcoding.

## Enforcement

1. **Backend is authoritative.** Every resource route calls `authorize_resource(resource)` → `require_permission(user, "{prefix}.{action}")`. Action derived from HTTP method + path suffix (see BACKEND.md).
2. **Creator scope** (`modules/record/services/creator_scope.py`): for record resources,
   - unrestricted roles (`core/privileged.py`) bypass;
   - if a role's `{prefix}.{action}` row has `scope='creator'`, the user may only act on rows where `record.created_by` = their actor id (list filtering + per-row checks); `view` with creator scope also limits list surfaces.
3. **Record-type × organization access**: `record_type_permission` (organization_id × permission_kind) can grant/deny type usage per organization.
4. **Dashboard cache isolation**: per-user cache key (user id + permission fingerprint) — never serves one user's permission-filtered data to another.
5. **Frontend gating is UX-only**: `auth.canAccessPage(config.permission)` hides pages/actions; backend rejects anyway (403 without logout).

## Special rules

- `assign` action guards topic assign/reorder; `transition` guards stage moves; `comment` guards comments; `share` guards file sharing.
- SuperAdmin/unrestricted: `core/privileged.py` bypasses row-level checks (still audited).
- Login rate-limited (429); session timeout configurable per deployment (`sessionTimeoutMinutes`).

## Testing checklist

- [ ] Role without `view` gets 404/403 on list and detail
- [ ] `creator` scope: creator allowed, non-creator denied, unrestricted bypasses
- [ ] New record type appears in permission catalog and role matrix without deploy
- [ ] 403 does not log the user out; 401 triggers refresh
- [ ] Dashboard responses differ per permission set (cache isolation)
