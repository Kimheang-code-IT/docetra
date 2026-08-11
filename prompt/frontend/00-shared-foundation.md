# Prompt 00 — Shared Nuxt UI Foundation

> **Status:** Implemented — architecture reference only (not a build ticket).
> Key code: `layouts/default.vue`, `useMenu.ts`, `useUserMenu.ts`, `AppHeader*`, `AppSlidebar`, `stores/preferences.ts`, i18n, adapters, `useGlobalSearch`.

## Reference (was copy/paste prompt)

You are implementing the Docetra v2 frontend inside the existing `frontend/` directory. First inspect the current code, package versions, layouts, components, composables, stores, middleware, i18n files, and local conventions. Preserve useful existing infrastructure and unrelated user changes.

Use only the existing stack and versions from `frontend/package.json` / `prompt/frontend/README.md` Technology baseline: Nuxt `^4.3.1`, Vue `^3.5.29`, TypeScript `^5.9.3`, Nuxt UI `^4.5.1`, Tailwind CSS `^4.2.1`, Pinia `^3.0.4`, Nuxt i18n `^10.2.3`, VueUse `^14.2.1`, TanStack Vue Table `^8.21.3`, TipTap `3.29.2` (via Nuxt UI `UEditor`), Uppy 5.x (`@uppy/vue` `^3.2.0`), ECharts `^6.0.0`, Zod `^4.3.6`. Do not add a new UI framework, state library, chart library, or duplicate dependency. Pin all TipTap packages to `3.29.2` with `pnpm.overrides` so ProseMirror is not duplicated.

Build a reusable authenticated application shell matching this navigation:

**Sidebar (`useMenu.ts`):**

- Dashboard
- Meeting: Topic, History
- Record: Incoming Document, Outgoing Document, Document, Master List Request, Logs
- Organization: Department, Company, Company Purpose, Company Sector, Officer
- Portal: File Upload, Google Drive Sync, Logs
- User Management: Role, User
- Configuration: Record Type, Record Attribute
- Settings: App Info, App Config, Storage

**User menu (`useUserMenu.ts`):**

- System Log → `/system-monitor/system-logs` (not a sidebar item)
- Language (en / km)
- Font size (`sm` | `md` | `lg` | `xl` via `stores/preferences.ts`)
- About (`AppAboutDialog` + `runtimeConfig.public.appVersion`)
- Appearance (light / dark)
- Logout

Use Nuxt UI navigation components and Lucide icons already available through Iconify. Groups must be collapsible, keyboard accessible, responsive, and show the active child route. On small screens, use the existing dashboard/sidebar mobile behavior. Keep navigation data in one typed configuration source rather than duplicating it in templates. All user-facing labels must use i18n keys with English and Khmer entries; do not hardcode labels in page templates.

Page titles for Record / Portal logs use plural **Logs** (`docetra.pages.recordLog`, `docetra.pages.portalLog`) with routes `/records/record-logs` and `/portal/portal-logs`.

### App version and About

- Expose the product version through Nuxt runtime config: `runtimeConfig.public.appVersion`, sourced from `NUXT_PUBLIC_APP_VERSION` (fallback `0.1.0`) in `nuxt.config.ts`.
- Show the version on the user menu **About** dialog (`AppAboutDialog`) as a badge on the brand logo (for example `v0.1.0`). Do not invent a second version source in components.
- To bump the displayed app version, update `NUXT_PUBLIC_APP_VERSION` in the environment or the default in `nuxt.config.ts`. Prefer env for deploy pipelines.
- Keep About content light: brand, tagline, version badge, social links, copyright. Do not reintroduce framework/installed-apps dumps unless product asks for them.
- Default i18n locale is **English** (`defaultLocale: 'en'`). Persist language only when the user explicitly chooses Khmer or English (`preferences.setLocale`).

### Global search (Cmd+K)

- Mounted in `layouts/default.vue` via `UDashboardSearch` + `useGlobalSearch`.
- Modes: **keyword** (default) and **semantic**; Ask AI only on explicit user action.
- Hits come from the Phase 2 local file-text index (`utils/search/*`, `adapters/search.ts`), permission-filtered, with source links.
- Keep page-level `AppLiveSearch` for list/board filters — do not replace it with Cmd+K.

### Form controls

All `UInput`, `USelect`, `UTextarea`, `UInputDate`, `UInputNumber`, and `UCheckbox` use the soft elevated style by default (`variant: soft`, light gray fill, no hard ring). Configured globally in `frontend/app/app.config.ts`. Do not restyle individual fields unless a control needs a deliberate exception (e.g. ghost search). Use `UFormField` with `required` for the red asterisk. Checkboxes default to neutral (dark checked fill).

### Layout padding

- **List / main workspace pages** (dashboard, entity lists, settings placeholders, portal upload): main content shell uses `px-1.5 pt-1.5 pb-0`.
- **Document detail / create pages**: main content under the header uses `p-0` (edge-to-edge). Do not wrap detail pages in the list-page padding.
- Keep header/navbar horizontal inset aligned with the shell (`px-1.5` where Nuxt UI dashboard navbar is customized).

### Auth routes

- Canonical: `/auth/login`, `/auth/forget-password`, `/auth/verify-code`, `/auth/reset-password`.
- Legacy aliases `/login` and `/forget-password` redirect to the `/auth/*` routes.
- `middleware/auth.global.ts` treats both sets as public. Every other page declares a permission key and the middleware rejects authenticated users that lack it.
- Create pages use `.create`, list/detail pages use `.view`, and shared components separately gate edit/delete/comment/export/configure actions.
- Frontend checks never replace API authorization.

### Frontend security boundary

- All authenticated API calls must remain on `runtimeConfig.public.apiBase` origin; never forward bearer headers to a component-provided cross-origin URL.
- Use `utils/security/url.ts` for HTTP(S) external links, root-relative internal navigation, safe raster image sources, and same-origin API URL resolution.
- Use `utils/security/files.ts` for shared image/file allow-lists and size/type validation. SVG is not accepted for inline preview or rich-text insertion.
- Keep `SameSite=Strict`, root-path cookies and `Secure` cookies in production. Moving the auth token to HttpOnly requires backend session/refresh-cookie support and is the target production design.
- Mock credentials and mock password-reset behavior are temporary release aids. The current release defaults to mock mode; disable it when the real API is ready.
- Keep security response headers in `nuxt.config.ts`; introduce a CSP only after validating Nuxt inline assets, fonts, image origins, and editor behavior.

### Loading and performance

- Do **not** create custom page/table skeleton components.
- Use Nuxt UI defaults only: `UTable` `:loading` (header progress) for lists, and a light spinner overlay where a full table is not present.
- Keep TanStack / `UTable` virtualization for large datasets. Prefer stale-while-revalidate (keep rows visible while refreshing) over tearing down the table DOM.
- Never fetch an entire large table into the browser; keep server pagination.

### Data adapters & mock mode

- Entity CRUD: `adapters/createEntityAdapter.ts` + `config/entities.ts`.
- Configuration / settings: `useConfigurationRepositories()` / `useSettingsRepositories()` — mock localStorage in enabled mock mode, otherwise HTTP.
- Auth: `adapters/auth.ts`. Search: `adapters/search.ts`.
- Mock mode defaults on in the current release so the complete UI can be tested without a backend. Set `NUXT_PUBLIC_USE_MOCK_DATA=false` later to activate the existing HTTP repository path.

### Implement now

1. Create or update the shared shell and sidebar + user menu.
2. Keep every route listed in `prompt/frontend/README.md`.
3. Implement `00-reusable-workspace-components.md` before duplicating page UI.
4. Replace blank placeholders with the complete page composition defined by each page prompt.
5. Add typed page metadata, title keys, permission codes, API adapters, columns, filters, document schemas, and workflow stages.
6. Keep route files thin. Business pages configure reusable workspace and document-page components instead of copying tables, boards, forms, comments, or timelines.
7. Use realistic bounded mock adapters only when the backend endpoint is unavailable, and isolate them so real API integration is a direct replacement.
8. Do not replace the application blindly. Reuse compatible components and preserve unrelated user changes.

### Big-data UI architecture

All list and board pages must use:

- Server-side pagination, sorting, filtering, and search.
- Debounced search with request cancellation and stale-response protection.
- URL query parameters as the shareable source of list state.
- Stable row IDs and typed API response models.
- Bounded page sizes; never fetch an entire large table into the browser.
- Optional row virtualization only when pagination is insufficient.
- Nuxt UI default loading, empty state, error state, retry, and permission-denied state.
- Lazy-loaded heavy dialogs and charts.
- Access-aware actions, with the backend remaining the authorization source of truth.
- Accessible focus management, keyboard navigation, and responsive layouts.
- Cursor-paginated comments and activity.
- Bounded Kanban columns with incremental loading and optimistic transition rollback.
- Dedicated schema-driven `/new` and `/:id` document pages for create, detail, and edit.
- ERPNext-style document layout built only with Nuxt UI: sticky header/actions, a fixed non-vertical-scrolling section-tab row, independently scrolling active-tab content, responsive form grid, right metadata rail, comments, and activity. This shared behavior applies to add, edit, and detail modes.
- Per-row `⋯` action menus (`AppRowActionsMenu`) for Detail / Logs / Delete (permission-aware).
- Config-driven board card fields via App Config display settings.
- System-wide dynamic fields via the Attribute Catalog and versioned record-type schema in `00C-dynamic-record-fields.md`; this applies to meetings, meeting topics, documents, and future record-backed pages.

Follow `/api/v2` REST conventions from the specifications. Keep uncertain endpoint names behind typed adapters rather than spreading invented URLs through page components.

### Quality checks

Run the available typecheck and build commands. Fix errors caused by this work. Confirm that every sidebar link resolves, System Log opens from the user menu, active navigation works, group toggles work, English and Khmer keys exist, table/board state survives refresh, document forms are keyboard accessible, unsaved-change protection works, and permission-hidden actions cannot be triggered from the UI.

At completion, report the files changed, routes created, verification commands, and any pre-existing issue that prevented a clean check.
