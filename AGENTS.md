# Docetra (OpenCode / agent rules)

Administrative record platform. Unified `record` model differentiated by `record_type`. Meeting is a special record type with topic-container board behavior — not a separate product domain.

Work in this repo. Load the **`docetra`** skill for any feature, bug, or review.

## Source of truth (conflict order)

1. `prompt/specification/` — architecture, domains, APIs, module boundaries. Start: `00-overview.md`, `02-domain-model.md`, `07-data-model.md`, `modules/record.md`.
2. `prompt/idea/` — business goals and draft schema when the spec is silent.
3. `prompt/frontend/` — presentation/layout only; must not contradict idea + specification.
4. Shipped UI wins only until migrated to the unified model.

Do not invent a second domain for documents vs meetings vs files vs URLs.

## Stack

| Layer | Path | Notes |
| --- | --- | --- |
| Frontend | `frontend/` | Nuxt 4, Vue 3, Nuxt UI 4, Pinia, i18n en/km |
| Backend | `backend/` | FastAPI modular monolith, `/api/v2` |
| Compose | `compose.backend.yml` | API :8000, worker, scheduler; Postgres, Redis, RabbitMQ, MinIO |

Browser → Nuxt `:3000` → proxy `/api/v2` → FastAPI `:8000`. Empty `NUXT_PUBLIC_API_BASE` = same-origin proxy.

## Commands

Frontend (`frontend/`): `pnpm install` · `pnpm dev` · `pnpm typecheck` · `pnpm test:unit` · `pnpm lint`

Backend (`backend/`): `python -m pytest -q` (unit + contract) · `python -m pytest tests/integration -m integration -q` (Compose up)

Local API: `docker compose --env-file backend.env -f compose.backend.yml up --build -d`

Never commit `backend.env`, `.env`, or secrets.

## Product rules

- Cards/lists: summary + scan fields from type config (`title`, `status`, `record_stage` / stage, `record_tag` / tags, `record_time`, `record_content`).
- Prefer configuration over hardcoded per-type field lists.
- Menus/routes come from active types + `uiSurface` (`meeting` | `document` | `system`). Routes: `/meetings/{typeCode}`, `/records/{typeCode}`.
- Backend enforces permissions. Frontend `AuthUser.permissions` is display/gating only.
- Keep history append-oriented. Do not drop operational past state.

## Engineering rules

- Frontend: pages stay thin. Lists → `WorkspaceEntityWorkspaceView` / stage board. Show/create → `DocumentEntityDocumentView`. Meeting topics → `MeetingAppMeetingTopicBoard`. No one-off page scaffolds. All `$fetch` through adapters/`useApi()`. User-facing copy needs en + km i18n.
- Backend: logic in `backend/app/modules/<name>/{api,domain,services,repositories}/`. Do not run scheduler/worker work inside the API process. Redis is cache/session only — PostgreSQL is truth. Path/payload keys: frontend adapters win until a versioned API change.
- API connection / show-page smoothness: do not block first paint on a request waterfall. See skill file `connection.md`.
- Optimistic concurrency: send `version` / `If-Match` on updates. Do not invent a second locking scheme.
- Do not add a new UI framework, state library, or duplicate TipTap/Uppy/ECharts stack.

## Do not

- Hardcode a Vue page per record type.
- Trust the client for authorization.
- Put long Drive sync, exports, or notifications in an HTTP handler.
- Cache secrets or authorization proof in Redis as the source of truth.
- Commit live env files or credentials.
