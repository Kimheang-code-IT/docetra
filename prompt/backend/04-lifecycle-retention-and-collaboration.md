# Lifecycle, Retention, Activity, and Comments

This contract separates reversible archive, administrator-restorable soft delete, and irreversible purge. The backend enforces ownership, role scope, dependencies, tenant boundaries, retention, and legal holds; frontend visibility is only a usability layer.

## 1. Canonical actions

| Action | Result | Normal user | Administrator |
| --- | --- | --- | --- |
| Archive | `status=archived`; data retained | May archive owned records with `.archive` and creator scope | May archive permitted records |
| Restore archived | `status=active` | May restore their own archived records with `.restore` and creator scope | May restore permitted archived records |
| Delete | `status=deleted`; hidden tombstone | May soft-delete owned records with `.delete` and creator scope; cannot self-restore deleted data | May soft-delete and restore deleted data with `.restore` at administrator scope |
| Purge | Physical removal/anonymization after checks | Never | Requires `.purge`, step-up confirmation, reason, and policy checks |

`purge` is never compatible with creator-only scope. It is not implied by `.delete`, super-user UI visibility, or ownership. The API returns `409` when dependencies, retention, legal hold, last-administrator protection, or active workflow rules prevent purge.

Every lifecycle mutation includes expected entity version, reason where required, actor, tenant, and idempotency key. Normal `DELETE /resource/{id}` is soft delete. Permanent removal uses explicit `DELETE /resource/{id}/purge`.

## 2. Roles and user accounts

### User account

- A user selecting “Delete/deactivate my account” gets `status=disabled`; all sessions and reset tokens are revoked and login is blocked. This is not a self-service purge.
- An administrator may reactivate a disabled account after authorization and audit review.
- An administrator may mark an account deleted, then purge/anonymize it only under retention policy. Historical audit events keep a non-secret stable actor reference even when personal fields are anonymized.
- The last active administrator cannot disable, delete, or purge themselves.

### Role

Roles are shared administrator-managed configuration, not user-owned records. A normal user cannot archive, restore, delete, or purge the role assigned to them.

- Archive prevents new assignment but preserves current references until migrated.
- Restore makes an archived role assignable again.
- Delete creates a tombstone.
- Purge requires zero assigned users and cannot remove the last role capable of security administration.

## 3. Meetings and topics

- Owner/creator-scoped users may archive and restore their own meetings/topics when policy permits.
- Archive removes the card from active boards and pauses/removes future APScheduler reminders. Restore rebuilds future eligible schedules.
- Soft delete cancels future schedules and pending notifications; administrators may restore and reconcile schedules.
- Topic delete must reject, reassign, or explicitly include child meetings according to the confirmed request—never silently orphan them.
- Purge removes meeting/topic content, recurrence instances, links, comments, and attachments through coordinated storage cleanup, while retaining the minimum immutable purge audit allowed by policy.

## 4. Documents and record workflow

- Lifecycle and workflow stage remain separate. Archive freezes transitions and preserves the last `stageId`.
- Restore returns the document to Active at its preserved stage unless the configured workflow requires a safe recovery stage.
- Soft delete blocks transitions, assignment, comments, and new attachments but preserves the full history for administrator recovery.
- Purge requires retention/legal-hold checks and coordinated attachment/object deletion. Numbering/reference values are never silently reused unless an explicit numbering policy permits it.

## 5. Activity and comments

Every supported resource—including meetings, topics, documents, users, roles, configuration, and master data—exposes permission-filtered Comments and immutable Activity where the UI enables collaboration.

Activity events are generated for create, view-sensitive export where required, update, assignment, share, stage transition, archive, restore, soft delete, administrator recovery, purge request/result, comment add/edit/delete, attachment change, notification routing, and permission/configuration changes. Events include stable action code, safe summary, actor, time, correlation ID, entity version, and redacted metadata.

- Activity cannot be edited or deleted through ordinary APIs.
- Comment authors may edit/delete their own comments when policy permits; moderators use `.comment` with elevated scope.
- Comment add/edit/delete creates its own activity event. Deleted comment bodies are not copied into activity metadata.
- Deleted resources are read-only except administrator restore/purge and authorized audit access.
- Purge removes user content as required while a minimal content-free purge audit remains in the system audit store.

## 6. API surface

For lifecycle-enabled resources:

| Method | Path | Permission |
| --- | --- | --- |
| POST | `/{resource}/{id}/archive` | `{namespace}.archive` plus ownership/scope |
| POST | `/{resource}/{id}/restore` | `{namespace}.restore`; deleted recovery requires admin scope |
| DELETE | `/{resource}/{id}` | `{namespace}.delete`; soft delete only |
| DELETE | `/{resource}/{id}/purge` | `{namespace}.purge`; administrator only |
| GET/POST | `/{resource}/{id}/comments` | `.view` / `.comment` |
| PATCH/DELETE | `/{resource}/{id}/comments/{commentId}` | Author or moderator `.comment` scope |
| GET | `/{resource}/{id}/activity` | `.view` plus field/event redaction |

List APIs exclude archived/deleted rows by default. There is **no** dedicated `/archive` collection. The Archive workspace lists each source twice with `status=archived` and `status=deleted`. Those filters are required.

## 7. Verification

- Owner archive/restore succeeds only for owned rows.
- Owner soft delete cannot self-restore deleted rows.
- Administrator restores deleted rows; ordinary users cannot.
- Purge requires explicit `.purge`, reason, confirmation, dependency/retention checks, and cannot use creator-only scope.
- Meeting schedule cancellation/rebuild and document stage preservation are tested.
- Role assignment and last-admin protections are tested.
- Every action produces a safe immutable activity event; comment permissions and redaction are tested.

## 8. Frontend contract

| Concern | Code |
| --- | --- |
| Archive workspace | `frontend/app/composables/archive/useArchiveWorkspace.ts` |
| Entity lifecycle | `frontend/app/adapters/createEntityAdapter.ts` (`archive`, `restore`, `delete`, `purge`) |
