# Docetra — agent guide

Docetra is one unified `record` domain differentiated by `record_type`. Meeting is a special
record type (topic-container behavior) — not a separate document/meeting/file/URL domain.
Backend authorization is authoritative; frontend `AuthUser.permissions` gates presentation only.

## Repo map

- `backend/` — FastAPI API + RabbitMQ worker + APScheduler (one entry `app.main`, three processes).
- `frontend/` — Nuxt 4 / Vue 3 / Nuxt UI 4 / Pinia / Tailwind 4 app.
- `infrastructure/` — Docker Compose (nginx, api, worker, telegram, postgres, redis, rabbitmq, minio) + ops scripts. nginx is the sole edge: serves the static SPA and proxies `/api/` → FastAPI. APScheduler runs in the API (`SCHEDULER_IN_API=true`); the Telegram bot runs in its own `telegram` container.
- `docs/specification/` — **source of truth** for domain, API, permission, and data rules; module docs in `docs/specification/modules/`.
- `docs/BACKEND.md`, `docs/FRONTEND.md` — detailed current-behavior references.
- `.pi/skills/docetra-*` — per-module domain skills; load the matching one before changing a module.

## Commands

Backend (from `backend/`):

```powershell
pip install ".[test]"
python -m pytest -q                                      # unit + contract + architecture; skips integration
python -m pytest tests/architecture -q                   # ownership + module-DAG ratchets (run after backend edits)
python -m pytest tests/unit/modules/record -q            # one module
python -m pytest tests/integration -m integration -q     # needs running Compose API (DOCETRA_API_BASE)
ruff check app tests                                     # CI lint (line-length 140)
python -c "import app.main"                              # import smoke test
```

Frontend (from `frontend/`):

```powershell
pnpm install            # postinstall runs `nuxt prepare`; typecheck needs the generated .nuxt
pnpm dev                # port 3000, host 0.0.0.0
pnpm typecheck          # nuxt typecheck
pnpm lint               # eslint .
pnpm test:unit          # vitest run
pnpm test:e2e           # playwright; needs backend + built app
pnpm build              # Nitro preset `vercel`; CI/e2e sets NITRO_PRESET=node-server
pnpm generate           # NUXT_STATIC_SPA=true static build served by nginx (Docker image)
```

Full stack (from repo root; Compose auto-loads `infrastructure/.env`):

```powershell
docker compose -f infrastructure/docker-compose.yml up --build -d
```

CI (`.github/workflows/ci.yml`): gitleaks → backend lint/unit/contract → frontend lint/typecheck/unit → live integration → migrations. CD (`.github/workflows/cd.yml`) runs on CI success: `promote` (merge tested `dev` into `main`), `build` (push backend + frontend images to GHCR: `sha-<short>`, branch, `latest` on main), `deploy` (SSH pull-only — `docker compose pull` + `up -d --no-build`; the server never builds). Secrets/vars in `docs/DEPLOYMENT.md`.

## Backend rules

- Layering: `Router → Application Workflow/Service → Repository → Database`. Services own rules but never `commit()`; repositories own SQL/flush; routers/workflows own transactions.
- Cross-module calls use `Service → Service` through public facades only: `service`, `schema`, `exceptions`, `dependencies`.
- Approved module DAG (enforced by `tests/architecture/test_module_dependencies.py`):
  `reporting_support → record, organization, people_access, storage_integration`;
  `storage_integration → record, admin_config`; `record → organization, people_access, admin_config`;
  `organization → admin_config`; `people_access → admin_config`; `admin_config → none`.
- `core`, `shared`, `integrations`, `platform` must import no business module. Platform audit/messaging is the only way to touch audit/outbox tables.
- One canonical mapped class per table, defined in its owner `model.py` (`app/modules/*/model.py`, `app/platform/{audit,messaging}/model.py`). The legacy `app.models` package is deleted — never reintroduce it or re-export models from `app/db`.
- `app/db/metadata.py` is the sole SQLAlchemy registration aggregator; Alembic imports it, never model modules directly.
- Significant mutations are audited; history stays append-only. Responses use the `{data, meta}` envelope; domain errors map to 400/401/403/404/409/422/429/500 without leaking stack traces.
- Worker jobs (Drive sync, exports, notifications, scans) never run inside the API process. APScheduler runs in-API only when `SCHEDULER_IN_API=true` (small single-process deploys); use a standalone `python -m app.main scheduler` process otherwise.

## Frontend rules

- Keep pages thin. Lists use `WorkspaceEntityWorkspaceView` (or `RecordAppRecordStageBoard`); create/detail/edit use `DocumentEntityDocumentView`; meeting topics use `MeetingAppMeetingTopicBoard`. Extend these instead of adding one-off scaffolds.
- All HTTP goes through `useApi()` / entity adapters / `app/repositories/*`. No component-level `$fetch`, `fetch`, or Axios. Endpoint constants live in `app/utils/constants/api-endpoints.ts`.
- Menus and routes derive from active record types (`/meetings/{typeCode}`, `/records/{typeCode}`), not hard-coded type codes. `app/config/entities.ts` is the central entity/workspace config.
- Preserve optimistic concurrency with `version` + `If-Match` (`withConcurrencyToken`).
- Every new user-facing string needs both `en` and `km` keys in `frontend/i18n/locales/`.
- Do not add a new UI framework, state library, editor, uploader, or chart stack.

## Gotchas

- `AGENTS.md` and older docs may reference `prompt/`; the real spec tree is `docs/specification/`.
- Migrations live in `backend/alembic/versions`; current head is `0012_drop_favorites`. Never edit a shipped revision, and do not add a migration just to move Python model definitions.
- Architecture tests fail on: `app.models` imports, models imported through `app.db`, cross-module imports outside public facades, hidden function-level cross-module imports, services calling `commit()`, and DAG drift.
- `useApi()` captures Nuxt app state and must be created while setup context is active. Calling it from delayed callbacks throws `NUXT_E1001` — capture clients during setup/plugin/store creation, or use `nuxtApp.runWithContext()` for genuinely delayed work. DevTools is disabled in `nuxt.config.ts` to silence the unrelated `[nostics]` warning.
- Never commit `infrastructure/.env`, `frontend/.env`, `backend.env`, credentials, or secrets — CI runs gitleaks.
