# Prompt 00 — Shared Nuxt UI Foundation

## Copy/paste prompt

You are implementing the Docetra v2 frontend inside the existing `frontend/` directory. First inspect the current code, package versions, layouts, components, composables, stores, middleware, i18n files, and local conventions. Preserve useful existing infrastructure and unrelated user changes.

Use only the existing stack: Nuxt 4, Vue 3, TypeScript, Nuxt UI 4, Tailwind CSS 4, Pinia, Nuxt i18n, VueUse, TanStack Vue Table, and ECharts. Do not add a new UI framework, state library, chart library, or duplicate dependency.

Build a reusable authenticated application shell matching the supplied sidebar structure:

- Dashboard
- Meeting: Topic, History
- Record: Incoming Document, Outgoing Document, Document, Master List Request, Log
- Organization: Department, Company, Company Purpose, Company Sector, Officer
- User Management: Role, User
- Configuration: Record Type, Record Attribute, Document Type
- Portal: File Upload, Google Drive Sync, Log
- System Monitor: System Log

Use Nuxt UI navigation components and Lucide icons already available through Iconify. Groups must be collapsible, keyboard accessible, responsive, and show the active child route. On small screens, use the existing dashboard/sidebar mobile behavior. Keep navigation data in one typed configuration source rather than duplicating it in templates. All user-facing labels must use i18n keys with English and Khmer entries; do not hardcode labels in page templates.

### Implement now

This is only the route-scaffolding pass:

1. Create or update the shared shell and sidebar.
2. Create every route listed in `prompt/frontend/README.md`.
3. Each page must render inside the shared shell.
4. Each page must contain only:
   - a reusable page header with title and optional breadcrumb;
   - a subtle Nuxt UI placeholder/empty-state card saying the page is ready for UI implementation.
5. Add typed page metadata where useful, including title/permission code.
6. Do not call APIs, generate mock business rows, or build final tables/forms/charts.
7. Do not place all page logic in one component. Keep each Nuxt route as a small independent page.
8. Do not replace the whole application blindly. Reuse components and conventions that remain compatible.

### Architecture for the later big-data UI

Prepare the structure so future list pages can use:

- Server-side pagination, sorting, filtering, and search.
- Debounced search with request cancellation and stale-response protection.
- URL query parameters as the shareable source of list state.
- Stable row IDs and typed API response models.
- Bounded page sizes; never fetch an entire large table into the browser.
- Optional row virtualization only when pagination is insufficient.
- Loading skeletons, empty state, error state, retry, and permission-denied state.
- Lazy-loaded heavy dialogs and charts.
- Access-aware actions, with the backend remaining the authorization source of truth.
- Accessible focus management, keyboard navigation, and responsive layouts.

Follow `/api/v2` REST conventions from the specifications, but do not invent or integrate endpoints during this scaffold pass.

### Quality checks

Run the available typecheck and build commands. Fix errors caused by this work. Confirm that every sidebar link resolves without a 404, active navigation works, group toggles work, English and Khmer keys exist, and no page starts an API request.

At completion, report the files changed, routes created, verification commands, and any pre-existing issue that prevented a clean check.
