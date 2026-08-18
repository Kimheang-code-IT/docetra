# Frontend API integration guide

The frontend is mock-first but API-ready. Pages and components must not call `$fetch` directly or contain API endpoint strings.

## Enable the backend

Set these environment values and restart Nuxt:

```env
NUXT_PUBLIC_USE_MOCK_DATA=false
NUXT_PUBLIC_API_BASE=https://api.example.com
NUXT_PUBLIC_AUTH_MODE=cookie
```

Every endpoint already includes `/api/v2`, so `NUXT_PUBLIC_API_BASE` must contain only the API origin (and an optional deployment base path), without appending `/api/v2`.

## Request flow

```text
Page/component
  -> composable
  -> typed repository or adapter
  -> useApi
  -> configured API origin
```

- `app/utils/constants/api-endpoints.ts` is the only endpoint catalog.
- `app/composables/useApi.ts` is the only `$fetch` caller. It sends credentialed session cookies, adds CSRF headers to mutations, compacts query values, cancels stale requests, and handles 401/403 dialogs globally. Bearer headers are used only when `NUXT_PUBLIC_AUTH_MODE=bearer` is explicitly selected.
- `app/repositories/contracts/` defines Settings and Configuration contracts.
- `app/repositories/mock/` and `app/repositories/http/` implement the same contracts.
- `app/adapters/createEntityAdapter.ts` provides the shared CRUD, stage, comments, activity, attachment, neighbor, and favorite boundary for entity pages.
- `app/adapters/index.ts` selects entity endpoints and mock datasets without leaking the selected data mode into pages.

## Response contract

Entity list endpoints return:

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 0,
    "totalPages": 0
  }
}
```

Single-resource and mutation endpoints return `{ "data": { ... } }`. Errors should return a meaningful `message` with the correct HTTP status. Use `401` for an expired or invalid session and `403` for an authenticated user without permission; the shared API client displays the required dialog.

List endpoints accept bounded `page`, `limit`, `q`, `sort`, stage/status filters, and date range query values. The backend remains responsible for authorization, filtering records to the user's scope, and validating every mutation.

Safe server-side GET acceleration uses the Redis policy in `prompt/backend/01-cache-and-messaging.md`. Cache keys must include tenant and permission scope, and mutations invalidate affected details, lists, counts, search results, and dashboards after commit. The frontend does not need to know whether a response was a cache hit.

Long-running file, Drive, export, notification, or indexing work returns `202` with `{ "data": { "jobId": "...", "status": "pending" } }`. RabbitMQ workers process these jobs; frontend polling uses backoff and stops when the job finishes, the page is hidden, or the user navigates away.

Meeting timers are backend-owned by APScheduler. Meeting responses may include `timezone`, `reminderOffsetsMinutes`, `nextScheduledActionAt`, and `scheduleState`; the browser displays these fields but never registers the authoritative reminder or recurrence timer.

Meeting Telegram alerts and forgot-password email are backend integrations. The frontend manages only verified/allowlisted group destinations, per-user channel/reminder/quiet-hour preferences, and provider configured status; it never receives Telegram bot tokens, SMTP credentials, webhook secrets, or raw provider errors. Meeting alerts and development/IT alerts use separate bots and destination allowlists.

Future Google Workspace support uses backend-owned OAuth/PKCE redirects and provider adapters. The frontend may display safe capability/connection state and start connect, revoke, test, meeting-calendar sync, or Drive-picker actions, but it never stores Google access/refresh tokens or calls Google APIs with application credentials. Google Sign-In, Calendar, Drive, and Gmail are separate opt-in capabilities; see `prompt/backend/05-google-workspace-integration.md`.

Entity lifecycle endpoints are explicit: `POST /{id}/archive`, `POST /{id}/restore`, `DELETE /{id}` for recoverable soft delete, and `DELETE /{id}/purge` for administrator-only irreversible removal. The API must enforce ownership for self-service archive restore, hide tombstones from normal users, revoke sessions when a user disables/deletes their own account, and retain immutable activity for every lifecycle and comment mutation.

## Backend handoff checklist

1. Implement endpoints from `app/utils/constants/api-endpoints.ts`.
2. Match the TypeScript models under `app/types/docetra/` and repository contracts.
3. Implement `/auth/login`, `/auth/me`, and `/auth/logout` with an HttpOnly session cookie, CSRF protection, and consistent 401/403 responses.
4. Keep all list operations server-paginated; never require the frontend to fetch an entire dataset.
5. Verify uploads accept multipart requests at the configured same-origin endpoint.
6. Run the frontend with mock mode disabled and test list, detail, create, archive/restore, soft delete/admin restore, administrator purge, permissions, session expiry, comments/activity, attachments, export, and search.
7. Test short/long cache invalidation and RabbitMQ job success, retry, duplicate delivery, dead-letter, and recovery paths.

When an API shape changes, update the repository/adapter implementation and its type—not individual pages.

## Frontend quality checks

Run these before backend handoff or deployment:

```bash
pnpm typecheck
pnpm typecheck:unused
pnpm build
```

The unused-code check prevents dormant imports, variables, parameters, and implementation branches from accumulating again.
