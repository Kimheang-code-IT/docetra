# Docetra — Gap Analysis

Based on full inspection (code-verified unless noted). Severity: 🔴 high, 🟡 medium, 🟢 low.

## Consistency findings (frontend ↔ backend ↔ database)

| # | Finding | Severity | Evidence |
|---|---|---|---|
| 1 | **Vocabulary/enums API dead code** — ✅ **FIXED**: dead `CONFIGURATION_ENUMS*` constants removed from `api-endpoints.ts`. | ✅ | api-endpoints.ts |
| 2 | **Duplicate config tables**: `setting` (13 cols) and `settings` (3 cols) coexist. ⏸ **Deferred** — requires a coordinated migration on real data (0013). | 🟡 | DATABASE.md |
| 3 | **`menu` table seeded but unused by frontend**: navigation derives from record surfaces; `seed_menus` writes rows nothing reads (or only legacy consumers). | 🟢 | people.py, useRecordSurfaces |
| 4 | **Column naming quirk `nam`** on file/organization/officer/role/record_type etc. — works but error-prone; document-only (do not rename without migration plan). | 🟢 | models |
| 5 | **Legacy fields on `users`**: `role` (string) and `permissions` (JSON) coexist with `role_id` + `permission` rows. Legacy columns should be treated read-only/removed eventually. | 🟡 | users model |
| 6 | **Search**: keyword-only by design and honestly labeled; no semantic mode. `Ask AI` placeholder returns `available:false` + real citations. Intentional — keep until an AI provider is approved. | 🟢 (by design) | reporting_support/services/search.py |
| 7 | **Drive sync duplicate-job guard** — ✅ **VERIFIED OK**: `find_drive_job` matches only `queued\|processing`; re-sync after completed/failed works; worker retries up to `job_max_retries` then marks failed. | ✅ | drive_sync.py, consumers/__init__.py |
| 8 | **Backend assign-topic trusts topicId** — ✅ **FIXED**: `_resolve_topic` validates existence, type (`meeting_topic`), and active status on assign/reorder (422/404). Unit-tested. | ✅ | services/meeting.py |
| 9 | **Topic deletion orphan behavior** — ✅ **FIXED**: deleting/purging a topic clears `parent_record` + `topicId` details on child meetings (they surface in the Unassigned pool). Unit-tested. | ✅ | services/record_collections.py |
| 10 | **CI coverage floor 35%** — still open; unit coverage added for topic rules. | 🟢 | ci.yml |
| 11 | **No frontend Dockerfile** — ✅ **FIXED**: `frontend/Dockerfile` added (multi-stage node build → non-root runtime, `NUXT_PUBLIC_API_BASE` aware). | ✅ | frontend/Dockerfile |
| 12 | **E2E (Playwright) breadth**: config existed with no specs — ✅ **FIXED**: `frontend/e2e/smoke.spec.ts` added (8 UI smoke specs: login render, login→dashboard, topics board, incoming/combined documents, departments, record types, auth-guard redirect). All passing against the live stack. | ✅ | frontend/e2e |
| 13 | **`file.nam` vs UI `fileName`** mapping handled in serializers; consistent but fragile. | 🟢 | entities config |
| 14 | **Officer deletion with linked user/records** — guarded by FK, but UX for blocked deletes (error copy) not verified at runtime. | 🟢 | model FKs |

## Security review snapshot

✅ Strong: HttpOnly cookie sessions + CSRF, per-user dashboard cache isolation, creator-scope enforcement, redaction, rate limiting, container hardening, gitleaks, backend-authoritative permissions.
✅ **Architecture violation fixed**: `people_access/services/people.py` imported `organization.model` directly (breaking the approved DAG). Now resolves org names via a composition-root injected resolver (`register_organization_names_resolver` wired in `app/main.py` to `organization.service.names_by_ids`). Architecture tests: **14/14 pass**.
🟡 Watch: creator-scope covers record resources only (org/officer/user rows rely on plain permissions — acceptable); storage provider credentials encrypted but verify redaction on GET responses at runtime; JWT secrets require strong values in prod (enforced only by convention).

## UX observations

✅ Optimistic concurrency with rollback toasts; permission-gated row actions; combined document view; archive with restore; unassigned pool for meetings.
🟡 Export polling backoff and board request-count optimizations documented in AGENTS.md mission but **verify current behavior at runtime** before marking done.

## What is intentionally NOT a gap

- Keyword-only search / Ask-AI placeholder (honest, no fake AI).
- No enum vocabulary tables (removed deliberately in 0011; frontend constants should be deleted, not the API resurrected, unless product re-requires it).
- Entity-table generic engine — by design.
