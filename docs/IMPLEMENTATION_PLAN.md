# Docetra — Recommended Implementation Plan

Status after improvement pass (all gates run):

| Phase | Status |
|---|---|
| 1 — Dead code & contract cleanup | ✅ DONE (enum constants removed) |
| 2 — Data-integrity hardening | ✅ DONE (topic validation, child detach on delete; drive guard verified already correct) |
| 3 — Model hygiene (migrations) | ⏸ DEFERRED — requires coordinated migration on real data; needs user approval + live DB |
| 4 — Testing uplift | 🟡 PARTIAL (topic-rules unit tests added; broader uplift remains) |
| 5 — Performance verification | ✅ VERIFIED (export backoff, archive parallel+filtered, stage board 2 requests — all already implemented) |
| 6 — Deployment polish | ✅ DONE (frontend Dockerfile added) |
| Extra — Architecture repair | ✅ DONE (people_access→organization model import removed via DI; `HTTPException` import fixed; architecture 14/14, backend 168 passed, ruff clean) |

## Phase 1 — Dead code & contract cleanup (low risk, quick wins)

1. **Remove dead enum constants** in `frontend/app/utils/constants/api-endpoints.ts` (`CONFIGURATION_ENUMS*`) and any fallback vocabulary usage — backend has no such routes (GAP #1).
   - Gate: `pnpm typecheck && pnpm test:unit`.
2. **Delete or use `seed_menus`** — either consume `menu` table or stop seeding (GAP #3).
   - Gate: backend unit tests.

## Phase 2 — Data-integrity hardening (medium risk)

3. **Server-side assign-topic validation** (GAP #8): in `modules/record/services/meeting.py`, verify the target topic exists, is `meeting_topic`, and is active before persisting; reject with 404/422 otherwise.
   - Add contract test: assign to nonexistent/archived topic → 4xx.
4. **Topic deletion clears children** (GAP #9): on topic delete/archive, null `topicId` in child meetings (transactional, same router) so the Unassigned pool stays truthful.
5. **Drive sync single-active-job guard** (GAP #7): in `create job` path, reject if a queued/running job exists for the source (409), and add retry-from-failed semantics.
   - Gate: integration test with fake Drive.

## Phase 3 — Model hygiene (needs migration — plan carefully)

6. **Consolidate `setting` vs `settings`** (GAP #2): migrate app-info rows into `setting` (or vice versa), keep one canonical table, additive migration `0013_...` + backfill; update admin_config repositories.
7. **Deprecate legacy `users.role` / `users.permissions`** (GAP #5): stop writing them, then drop in a later migration after confirming no consumers.
8. Rename `nam` → `name`: **only** as a coordinated migration with DTO aliases; low priority, defer until other phases stabilize (GAP #4).

## Phase 4 — Testing uplift

9. Add the missing test list from TESTING.md (creator-scope e2e, cache isolation, attachment lifecycle, 409 flows, Drive lifecycle, stage validation, provider flows).
10. Raise CI coverage floor 35% → 55% incrementally.
11. Add Playwright happy-path specs: login → topic → meeting → complete; incoming doc → stage → archive.

## Phase 5 — Performance verification (AGENTS.md mission items)

12. Runtime-verify and, if needed, implement: archive request-count reduction (single filtered request per source), stage-board single dataset call, dashboard client-side refetch guard, export polling backoff (1.5s→2s→3s→5s, stop on terminal states).
    - Measure with network timeline before/after; no redesign.

## Phase 6 — Deployment polish

13. Optional frontend Dockerfile (multi-stage pnpm build → nginx) for one-command deploys.
14. Document/automate scheduled backups (cron example in infrastructure/scripts).

## Non-goals (do not do without product approval)

- Do not add semantic/AI search providers.
- Do not resurrect `/configuration/enums` API unless the product re-requires vocabulary management.
- Do not rename public API contracts or stable codes.

## Suggested execution order

```
1 → 2 → 3 → 4 → 5 → 6 (each with its test gate; commit per item)
```

Estimated effort: Phase 1 (0.5d), Phase 2 (1–2d), Phase 3 (2–3d incl. migration tests), Phase 4 (2–3d), Phase 5 (1–2d), Phase 6 (1d).
