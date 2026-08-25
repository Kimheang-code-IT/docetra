---
name: docetra
description: Implements and reviews Docetra end-to-end — unified records, Nuxt 4 UI, FastAPI modules, adapters, permissions, cache/workers, and API connection / show-page performance. Use when building, fixing, or reviewing any Docetra feature, frontend page, backend module, record show/detail page, slow UI, or /api/v2 connection.
compatibility: opencode
metadata:
  audience: engineers
  product: docetra
---

# Docetra

Follow [AGENTS.md](../../../AGENTS.md). Read the matching reference file before editing code.

| Work | Read |
| --- | --- |
| Product / schema / record types | [product.md](product.md) |
| Nuxt pages, UI, adapters, i18n | [frontend.md](frontend.md) |
| FastAPI modules, cache, workers | [backend.md](backend.md) |
| Slow UI, show page, `$fetch`, session | [connection.md](connection.md) |

## Workflow

Copy and track:

```
Task:
- [ ] Identify surface (record / org / people / storage / config / reporting / shell)
- [ ] Read spec + existing code in that module (do not scan the whole repo)
- [ ] Reuse workspace/document/meeting shells and module services
- [ ] Keep API paths/keys aligned with frontend adapters
- [ ] Parallelize independent reads; do not block paint on secondary GETs
- [ ] en + km i18n for new user-facing strings
- [ ] Verify: focused unit/contract tests; UI in the browser when the shell changed
```

## Implement

1. Spec first: `prompt/specification/` wins over idea docs; idea wins when spec is silent; `prompt/frontend/` is layout only.
2. Find the owner module. Put business rules there — not in Vue or in a shared grab-bag.
3. Records are one model (`record_type`). Meeting uses topic-container board behavior (`prompt/specification/modules/record.md`).
4. Frontend pages are routes only. Extend `config/entities.ts`, adapters, and shared components.
5. Backend HTTP stays thin. Services own rules; repositories own SQL; workers/scheduler own async and timers.
6. Connection: overlay waits only for the screen’s primary resource. Session, schema, comments, favorites, options, and neighbors are background or parallel. Coalesce in-flight identical GETs.

## Verify

- Frontend change: `pnpm test:unit` and `pnpm typecheck` from `frontend/`. Exercise the route in the browser when UI behavior changed.
- Backend change: `python -m pytest -q` from `backend/` (add `tests/integration` only if Compose is required).
- Do not commit `backend.env` or secrets.

## Examples

**New record type field on the show page** — extend record type attributes in configuration, not a new Vue page. Schema-driven tabs already merge type fields.

**List feels janky when filtering** — `NuxtPage` key must be `route.path`, not `route.fullPath`. Workspace already refetches from query.

**Show page spinner until comments load** — `useDocumentPage` must not hold `pending` for comments/activity/attachments. Only `adapter.get` blocks the form overlay.
