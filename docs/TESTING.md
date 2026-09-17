# Docetra — Testing

## Current test suites (verified)

### Backend (`backend/tests/`, 49 test files)

| Suite | Scope |
|---|---|
| `unit/` | Service/domain logic (numbering, lifecycle, creator scope, audit, validation) |
| `contract/` | API contract tests against route handlers (envelope, status codes, pagination) |
| `integration/` | Compose-backed flows (auth, records, attachments, exports) |
| `architecture/` | Dependency DAG rules: no `app.models`, no cross-module repo/model imports, no platform→business imports, metadata alignment |

Run:

```bash
cd backend
python -m pytest -q                 # unit + contract (integration deselected by default)
python -m pytest tests/architecture -q
python -m pytest tests/integration -q   # requires docker compose stack
python -c "import app.main"         # import smoke
```

CI gate: `pytest --cov=app --cov-fail-under=35`, plus `ruff check` and `compileall`.

### Frontend (`frontend/tests/unit/`, 9 files, 79 tests)

Covers: api endpoints contract (`api-endpoints.test.ts`), error policy (401/403 handling), badge/card fields, date filters, login errors, select display, stores/composables/components, form routing, board drag & drop.

```bash
cd frontend
pnpm typecheck     # nuxt typecheck (verified passing)
pnpm test:unit     # vitest (verified 79/79)
pnpm lint          # eslint
pnpm build         # production build
pnpm test:e2e      # playwright UI smoke (8 specs: login, dashboard, board, workspaces, auth guard)
```

E2E prerequisites: backend stack running (`DOCETRA_API_BASE`, default :8001 via frontend proxy) and an admin account (`ADMIN_EMAIL`/`ADMIN_PASSWORD` env; integration-test admin `admin@docetra.test` used in CI-less runs).
```

## What is covered vs. not

**Covered:** auth error policy, endpoint constants ↔ backend contract, board drag/drop logic, form routing, audit DTO mapping, record engine unit rules, architecture boundaries, **meeting topic assignment rules (`test_meeting_topic_rules.py`: validation + child detach)**.

**Gaps (recommend adding):**
- [ ] Creator-scope end-to-end tests (creator allowed / non-creator 403)
- [ ] Dashboard cache isolation test (different permission users)
- [ ] Attachment upload → download → detach lifecycle (integration)
- [ ] Meeting assign-topic + reorder concurrency conflicts (409 handling)
- [ ] Drive sync job lifecycle (queued → completed/failed) with fake Drive
- [ ] Stage transition validation per type (invalid stage rejected)
- [ ] Provider set-default/test-connection flows
- [ ] E2E happy paths: login → create topic → meeting → complete; incoming doc → stage → archive
