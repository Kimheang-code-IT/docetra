# Prompt 00 — Shared Nuxt UI Foundation

## Copy/paste prompt

You are implementing the Docetra v2 frontend inside the existing `frontend/` directory. First inspect the current code, package versions, layouts, components, composables, stores, middleware, i18n files, and local conventions. Preserve useful existing infrastructure and unrelated user changes.

Use only the existing stack: Nuxt 4, Vue 3, TypeScript, Nuxt UI 4, Tailwind CSS 4, Pinia, Nuxt i18n, VueUse, TanStack Vue Table, TipTap (via Nuxt UI `UEditor`), Uppy, and ECharts. Do not add a new UI framework, state library, chart library, or duplicate dependency. Pin TipTap packages to one version (e.g. `3.29.2`) with `pnpm.overrides` so ProseMirror is not duplicated.

Build a reusable authenticated application shell matching this navigation:

**Sidebar (`useMenu.ts`):**

- Dashboard
- Meeting: Topic, History
- Record: Incoming Document, Outgoing Document, Document, Master List Request, Logs
- Organization: Department, Company, Company Purpose, Company Sector, Officer
- User Management: Role, User
- Portal: File Upload, Google Drive Sync, Logs
- Configuration: Record Type, Record Attribute, Document Type
- Setting: App Info, App Config, Storage

**User menu (`useUserMenu.ts`):**

- System Log → `/system-monitor/system-logs` (not a sidebar item)
- Language, About, Appearance, Logout

Use Nuxt UI navigation components and Lucide icons already available through Iconify. Groups must be collapsible, keyboard accessible, responsive, and show the active child route. On small screens, use the existing dashboard/sidebar mobile behavior. Keep navigation data in one typed configuration source rather than duplicating it in templates. All user-facing labels must use i18n keys with English and Khmer entries; do not hardcode labels in page templates.

Page titles for Record / Portal logs use plural **Logs** (`docetra.pages.recordLog`, `docetra.pages.portalLog`).

### App version and About

- Expose the product version through Nuxt runtime config: `runtimeConfig.public.appVersion`, sourced from `NUXT_PUBLIC_APP_VERSION` (fallback `0.1.0`) in `nuxt.config.ts`.
- Show the version on the user menu **About** dialog (`AppAboutDialog`) as a badge on the brand logo (for example `v0.1.0`). Do not invent a second version source in components.
- To bump the displayed app version, update `NUXT_PUBLIC_APP_VERSION` in the environment or the default in `nuxt.config.ts`. Prefer env for deploy pipelines.
- Keep About content light: brand, tagline, version badge, social links, copyright. Do not reintroduce framework/installed-apps dumps unless product asks for them.
- Default i18n locale is **English** (`defaultLocale: 'en'`). Persist language only when the user explicitly chooses Khmer or English.

### Layout padding

- **List / main workspace pages** (dashboard, entity lists, settings placeholders, portal upload): main content shell uses `px-1.5 pt-1.5 pb-0`.
- **Document detail / create pages**: main content under the header uses `p-0` (edge-to-edge). Do not wrap detail pages in the list-page padding.
- Keep header/navbar horizontal inset aligned with the shell (`px-1.5` where Nuxt UI dashboard navbar is customized).

### Loading and performance

- Do **not** create custom page/table skeleton components.
- Use Nuxt UI defaults only: `UTable` `:loading` (header progress) for lists, and a light spinner overlay where a full table is not present.
- Keep TanStack / `UTable` virtualization for large datasets. Prefer stale-while-revalidate (keep rows visible while refreshing) over tearing down the table DOM.
- Never fetch an entire large table into the browser; keep server pagination.

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
- ERP-style document layout built only with Nuxt UI: sticky header/actions, section tabs, responsive form grid, right metadata rail, comments, and activity.
- Per-row `⋯` action menus (`AppRowActionsMenu`) for Detail / Logs / Delete (permission-aware).

Follow `/api/v2` REST conventions from the specifications. Keep uncertain endpoint names behind typed adapters rather than spreading invented URLs through page components.

### Quality checks

Run the available typecheck and build commands. Fix errors caused by this work. Confirm that every sidebar link resolves, System Log opens from the user menu, active navigation works, group toggles work, English and Khmer keys exist, table/board state survives refresh, document forms are keyboard accessible, unsaved-change protection works, and permission-hidden actions cannot be triggered from the UI.

At completion, report the files changed, routes created, verification commands, and any pre-existing issue that prevented a clean check.
