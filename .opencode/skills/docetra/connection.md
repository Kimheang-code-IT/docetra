# API connection and show-page load

The show/detail UI feels frozen when it **waits on a request chain**. Fix connection logic first; do not rewrite the whole page.

## Client

- All HTTP: `frontend/app/composables/useApi.ts` (timeout, CSRF, cookies, abort).
- Auth: `frontend/app/plugins/auth-session.client.ts` + `frontend/app/stores/auth.ts`.
- Show page: `frontend/app/composables/workspace/useDocumentPage.ts` + `DocumentEntityDocumentView`.
- Surfaces (menus + dynamic routes): `frontend/app/composables/record/useRecordSurfaces.ts`.
- Type schema: `frontend/app/composables/record/useRecordTypeDrivenTabs.ts`.
- Select options: `frontend/app/adapters/reference-options.ts`.

Local hop: browser → Nuxt `:3000` → FastAPI `:8000`. Empty `NUXT_PUBLIC_API_BASE` is correct. Do not set a full API origin unless the API is on another host.

## Required behavior

**Session**

- If a stored user exists, paint the shell. Re-check `GET /api/v2/auth/me` in the background.
- Call `POST /api/v2/auth/refresh` only when `/auth/me` returns **401**.
- Timeouts and 5xx must not wipe a working local session and must not add a second 30s wait.

**Show page**

- Overlay (`pending`) waits only for `adapter.get(id)`.
- Comments, activity, attachments, neighbors, favorite: start in parallel; fill in after paint.
- Do not keep the overlay up for record-type schema. Base tabs render; type fields merge when schema arrives.
- Load schema once. Cache by both type `code` and `id`. Reuse in-flight code lookup when the record id arrives.

**Shared GETs**

- Coalesce in-flight identical requests (record surfaces, schema, reference options).
- `cancelPrevious: true` is for replacing a stale search/list of the **same** resource. Do not abort a shared options/schema GET just because a second field mounted.

**Remount**

- `NuxtPage` `:page-key` uses `route.path`, not `route.fullPath`. Query-only updates (filters, sort, paging) must not destroy the page.

## Anti-patterns

```text
await /auth/me → await refresh on any error → await surfaces →
await record GET → await comments+activity+files → await schema (again by id) → paint
```

```text
documentPending = pending || loadingSchema   // blocks paint on secondary work
watch(route.query) + page-key=fullPath       // remount on every filter
requestKey shared + cancelPrevious           // second dropdown cancels the first
```

## Later (backend)

If the show page is still slow after the client waterfall is gone, add a single record GET that can include comments/files (versioned contract). Do not hide N+1 serializer cost behind more frontend spinners.

## How to check

DevTools → Network → open a record. Record GET, comments, activity, and files should overlap. The form should appear when the record GET finishes.
