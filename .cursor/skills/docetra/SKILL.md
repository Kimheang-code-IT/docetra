---
name: docetra
description: Implements and reviews Docetra end-to-end — unified records, Nuxt 4 UI, FastAPI modules, adapters, permissions, cache/workers, and API connection / show-page performance. Use when building, fixing, or reviewing any Docetra feature, frontend page, backend module, record show/detail page, slow UI, or /api/v2 connection.
---

# Docetra

This project skill is the Cursor entry point for Docetra. Follow `AGENTS.md` at the repo root. Then **Read** and follow the OpenCode skill (same workflow, shared references):

- `.opencode/skills/docetra/SKILL.md`

Load only the reference you need:

- `.opencode/skills/docetra/product.md` — spec vs idea, unified records, routes
- `.opencode/skills/docetra/frontend.md` — Nuxt shells, adapters, i18n
- `.opencode/skills/docetra/backend.md` — FastAPI modules, cache, workers
- `.opencode/skills/docetra/connection.md` — session, show-page waterfall, coalescing

## Workflow

```
Task:
- [ ] Identify surface (record / org / people / storage / config / reporting / shell)
- [ ] Read spec + existing code in that module (do not scan the whole repo)
- [ ] Reuse workspace/document/meeting shells and module services
- [ ] Keep API paths/keys aligned with frontend adapters
- [ ] Parallelize independent reads; do not block paint on secondary GETs
- [ ] en + km i18n for new user-facing strings
- [ ] Verify: focused tests; browser when UI behavior changed
```

Do not invent a separate domain for meetings vs documents. Do not add a Vue page per record type. Do not put worker/scheduler work in an HTTP handler.
