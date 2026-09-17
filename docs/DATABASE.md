# Docetra — Database

PostgreSQL is the business and authorization truth. Redis is cache/session only. Object bytes live in MinIO, never in the database.

**28 tables** (SQLAlchemy metadata, verified). Alembic head: `0012_drop_favorites` (migrations 0001–0012 in `backend/alembic/versions/`).

## Ownership map (canonical model locations)

| Module | Tables |
|---|---|
| `modules/record/model.py` | record_type, record_attribute, record_template, record_stage_template, record_type_permission, record, record_detail, record_attachment, record_organization, entities, comments, activities, meeting_schedules |
| `modules/organization/model.py` | organization, organization_sector, organization_purpose |
| `modules/people_access/model.py` | users, role, permission, menu, officer, officer_identifier |
| `modules/storage_integration/model.py` | file |
| `modules/admin_config/model.py` | setting, settings |
| `platform/audit` | audit_log, notification_audit_log |
| `platform/messaging` | outbox |

## Core tables

### `record` (22 cols)
`id, record_type_id, record_type_code, title, status, record_stage_id, stage, record_content (JSON), record_metadata (JSON), record_additional_info, record_time (indexed), record_tag, parent_record, record_flow_code, lifecycle, archived_at, deleted_at, created_by, updated_by, created_at, updated_at, version`

- One row per business item (meeting, topic, document, master list request).
- `record_time` is the configurable timeline field — resolution priority per type; **indexed** for mixed-timeline sorting.
- `version` = optimistic concurrency (matches `If-Match`).
- Lifecycle: `status` 1=active, 2=archived, 0=deleted; timestamps `archived_at`, `deleted_at`.

### `entities` (13 cols) — generic support-entity store
`id, resource, payload (JSON), stage, status, version, created_by, updated_by, created_at, updated_at, archived_at, deleted_at, record_time`

- Used by non-record resources: `record-logs`, `portal-logs`, `system-logs` (read-only), `file-uploads`, `google-drive-sync` (+ drive sync jobs as `kind: job` payloads), `drive-files`.
- Same envelope semantics (status/version/record_time) as `record`.

### `record_type` / `record_attribute` / `record_template` / `record_stage_template`
- `record_type`: `code` (unique, stable), `nam`, `description`, `payload` JSON (UI defaults: uiSurface, slug, icon, menuOrder, isCreatable, supportsStages, supportsTopicContainer, features), `deletable`, `is_active`.
- `record_attribute`: `code` (unique), `nam`, `data_type`, `payload` JSON (options, validation, visibility rules).
- `record_template`: mapping `record_type_id ↔ record_attribute_id` with `ordering`, `is_require`.
- `record_stage_template`: stages per type with `ordering`, `nam`, `is_final`.
- `record_type_permission`: `record_type_id ↔ organization_id` + `permission_kind` (organization-scoped type access).

### `record_detail` (dynamic attribute values)
`record_id, record_attribute_id, record_attribute_code, value_number, value_string, value_time, value_boolean, value_json, value_id` — typed columns per data type.

### `record_attachment` / `file`
- `record_attachment`: `record_id, reference_id, file_id` — pure business linkage (record ↔ file or record ↔ record).
- `file`: `nam, path, file_size, mime_type, storage_type, direct_url, source_table, status` + actor/timestamps. Bytes in MinIO; `source_table` marks origin (`drive-files` for synced Drive files). Deleting an attachment link does **not** delete the File/object; purge is explicit.

### `record_organization`
`record_id, organization_id, role_type` — links records to departments/companies (sender, recipient, owner unit, participant unit).

### `organization` / `organization_sector` / `organization_purpose`
- `organization` (21 cols): `nam, code, lvl, description, parent_id (hierarchy), sector_id, organization_purpose_id, organization_type (department|company), tax_id, address, contact_info, email, phone, logo_url, child_ids, is_active`.
- `organization_sector`: `nam, parent_id (sub-sectors), description, is_active`.
- `organization_purpose`: `nam, description, is_active`.

### `users` / `role` / `permission` / `menu` / `officer` / `officer_identifier`
- `users` (20 cols): `email, name, password_hash, role (legacy string), role_id, officer_id, avatar, phone, permissions (legacy JSON), active, status, version, last_login_at, app_metadata, user_metadata`.
- `role`: `nam, lvl, description, is_active`.
- `permission`: `role_id, code, is_enable, scope ('all'|'creator')` — one row per role×capability; `scope='creator'` restricts to self-created records.
- `menu`: seeded navigation codes (`parent_code, code, title, icon, ordering, is_menu`).
- `officer`: `nam, organization_id, role_id, auth_id (nullable → users), profile_url, email, is_active`; `officer_identifier`: typed identifiers.

### `meeting_schedules`
`meeting_id, job_key, run_at, kind, status` — reminder scheduling for meetings (worker/scheduler processed).

### Audit & messaging
- `audit_log` (12 cols): `action_code, table_name, row_id, detail_data JSON, ip_address, status_code, source_log, raw_text, message` — append-only.
- `notification_audit_log`: outbox notification processing trail.
- `outbox`: `topic, payload, processed_at, attempts` — transactional outbox for events.
- `activities` / `comments`: per-entity timeline (`entity_id, action, summary, actor_id, metadata, occurred_at`) and discussion (`entity_id, body, author_id, edited_at`).

### Config tables
- `setting` (13 cols): `key_group, key, description, data_type, public_access, visible, ordering, key_value` — app config (email, telegram, storage behavior).
- `settings` (3 cols): `key, value, updated_at` — app info (name, logo, etc.).

## Key relationships

```
record_type 1─n record (record_type_id)          record_type 1─n record_stage_template
record_type n─n record_attribute (via record_template, is_require, ordering)
record 1─n record_detail ─1 record_attribute     record 1─n record_attachment
record_attachment n─1 file                        record 1─n record_organization ─1 organization
organization ─1 organization_sector (self-parent) organization ─1 organization_purpose
organization 1─n organization (parent_id)         organization 1─n officer
users 1─1 officer (officer.auth_id / users.officer_id)
role 1─n permission                                role 1─n users (users.role_id)
record 1─n meeting_schedules
entities.payload: topicId/sortOrder on meeting rows; drive job payloads
```

## Conventions & invariants

- UUID primary keys everywhere; `created_by`/`updated_by` actor columns (officer or user id per table).
- Timestamps UTC; `record_time` drives timelines; `version` for optimistic locking.
- Codes (`record_type.code`, `record_attribute.code`, permission codes, `key_group/key`) are stable identifiers — renaming breaks contracts.
- Column naming quirk: `nam` (not `name`) on several tables — **do not rename** without a coordinated migration.
- Migrations: additive only in current policy; head `0012_drop_favorites` (0011 dropped enum vocabulary, 0012 dropped favorites).

## Consistency status (verified)

- SQLAlchemy metadata ↔ Alembic: aligned at head `0012`.
- Frontend expectations ↔ tables: record payloads (`topicId`, `topicTitle`, `sortOrder`, document fields) live in `record.record_content`/`record_metadata` JSON — typed accessors in `services/stamp.py` / `serializer.py`.
- ⚠ Two config tables (`setting` vs `settings`) coexist — see GAP_ANALYSIS.
- ⚠ `menu` table is seeded but the frontend builds navigation from record surfaces, not from `menu` — see GAP_ANALYSIS.
