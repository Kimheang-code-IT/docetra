# Prompt 00C — Dynamic Record Fields and Attribute Catalog

> **Status:** Frontend/mock form flow implemented across record-backed entities; schema-driven list/filter/search/card/export consumers and the production HTTP backend remain.
> **Product source:** `prompt/idea/` and `prompt/specification/`, especially the unified `record`, `record_type`, `record_attribute`, `record_template`, and typed `record_detail` model.
> **Existing foundation to extend:** `AppRecordAttributeList`, `AppRecordAttributeEditor`, `AppRecordTypeEditor`, `AppDynamicFieldRenderer`, `EntityDocumentView`, `useRecordTypeDrivenTabs`, and configuration repositories.

## Outcome

Authorized users can define a field once in a global **Attribute Catalog**, assign it to one or more record types, and configure where and how it appears. Every record-backed screen — including meetings, meeting topics, documents, master-list requests, and future record types — resolves its fields from the selected record type rather than from page-specific hardcoding.

The same resolved schema drives create, detail, and edit forms. It also supplies eligible custom columns, filters, search fields, board-card slots, exports, and future API validation. A newly published record type must therefore be usable without adding a new Vue page or changing a component switch statement unless it introduces a genuinely new field control or specialized workflow experience.

## Terminology and ownership

Use these terms consistently:

- **Attribute Catalog** — the reusable collection of field definitions (`record_attribute`). The existing `/configuration/record-attributes` route is this catalog.
- **Record Type** — a user-configurable category such as meeting, meeting-topic, document, or a future business record.
- **Type field assignment** — the mapping between a record type and a catalog attribute (`record_template` in the product model). It owns placement and type-specific overrides, not a duplicate attribute definition.
- **Resolved record schema** — the published, permission-filtered result of combining core fields, record-type configuration, catalog definitions, and assignment overrides.
- **Dynamic values** — values stored for a record's assigned attributes (`record_detail` in the product model; represented as an `attributes` object at the frontend boundary).

Do not call a catalog attribute an “attitude.” Use **attribute** or **custom field** in UI copy.

## System-wide rules

1. Apply this system to every entity backed by the unified `record` model, including Meeting and Meeting Topic. Do not limit it to incoming/outgoing documents, documents, and master-list requests.
2. Keep a small protected set of core fields for identity and lifecycle, such as record ID, record type, title, owner/organization context, status, stage, created/updated metadata, and schema version. Catalog fields cannot replace or shadow their codes.
3. Define a custom field once in the catalog and reuse it. Record types reference attributes by immutable ID and stable code.
4. Put record-type-specific settings on the assignment: required/read-only overrides, visibility, section/tab, order, width, create/detail/list/filter/card flags, and optional permission restrictions.
5. Use one resolved schema for add, detail, and edit. Mode and permission rules may change visibility or editability, but separate hardcoded forms must not drift apart.
6. The backend remains authoritative for schema, permissions, validation, defaults, and allowed values. Client rules improve UX but never grant authority.
7. Preserve unknown or temporarily hidden values when editing. Never erase a dynamic value merely because its field is not visible to the current user or its schema failed to load.

## Attribute Catalog UX

### Catalog list

Route: `/configuration/record-attributes`

Treat `AppRecordAttributeList` as a real catalog page with:

- server-side search, paging, sorting, status, data-type, and usage filters;
- exactly these catalog data columns, in order: **No.**, **Name**, **Code**, **Data Type**, **Updated At**, and **Updater**;
- actions for view/edit, duplicate, activate/deactivate, and view usage;
- status actions are contextual: an active row shows only **Deactivate**, while every non-active row shows only **Activate**;
- the Attribute Catalog and Record Type tables retain the shared row-meta column for updater, relative updated time, comment count, and favorite state;
- an **Add custom field** action;
- no hard delete when the attribute is published, assigned, or has saved values.

Selecting the usage count opens a panel or section listing the record types and placements using the attribute.

### Catalog editor

Routes: `/configuration/record-attributes/new` and `/configuration/record-attributes/:id`

The editor supports:

- identity: label, immutable code after first publish, description, help text, placeholder;
- data type and type-specific configuration;
- default value and null/empty behavior;
- validation rules;
- options for select-like fields with stable option values, localized labels, status, and order;
- capability flags: searchable, filterable, sortable, eligible for lists, eligible for board cards;
- sensitivity classification and optional view/edit permission codes;
- draft, published, and retired lifecycle states;
- a live field preview rendered by `AppDynamicFieldRenderer`.

Changing the data type or option values after records use the field requires compatibility validation and an explicit migration plan. Retiring an option prevents new selection but continues rendering its label for historical values.

## Record Type field composer

Route: `/configuration/record-types/:id`

Add a **Fields & layout** area to `AppRecordTypeEditor` that lets authorized users:

- search and add existing catalog attributes;
- create a catalog attribute without losing unsaved record-type work, then return and assign it;
- remove an assignment without deleting the catalog attribute or historical record values;
- reorder fields by drag-and-drop and keyboard controls;
- create/reorder tabs and sections;
- configure column width and placement;
- override allowed settings such as required, read-only, default, visibility, create/detail/list/filter/card exposure, and role/permission visibility;
- detect duplicate assignments, core-code collisions, invalid conditional dependencies, and circular visibility rules;
- preview create, detail, edit, table-row, and board-card modes at desktop and mobile widths.

The `/configuration/record-types` table exposes an **Assign fields** action on every row. It opens that record type directly on the Fields & layout tab. Assignment rows are sortable and each row can select an optional **Assigned stage**. An empty stage means the field applies for the complete record lifecycle; a selected stage means the field becomes applicable at that stage according to the runtime visibility/edit policy. Removing or renaming a stage must detect affected field assignments and require the administrator to reassign or clear them.

The Record Type editor exposes **General**, **Features**, **Attributes**, and, when enabled, **Workflow** tabs. It does not expose a Numbering tab. Any legacy numbering values may remain in the API model for backward compatibility but are not user-configurable from this editor.

Existing Record Type and Attribute detail pages include the shared Comments & Activity timeline. Create, update, activate, deactivate, comment add/edit/delete, assignment changes, and workflow changes must produce auditable activity events. Mock repositories implement the same `/comments` and `/activity` subresource contracts expected from the future HTTP API; create pages hide discussion until the first save creates an ID.

All normal entities use one schema-driven document implementation (`EntityDocumentView` + `useDocumentPage`) for add, detail, edit, update, save, reload, navigation, comments, activity, and attachments. Entity configuration controls layout such as wide content and metadata rail visibility; do not add entity-specific form-page implementations. For Meeting and Record entities, the resolved Record Type schema—not only the static base schema—must drive rendering and required-field validation in every mode. Dynamic values remain under `details`, and reload refetches both the record data and its current Record Type schema.

Mock mode intentionally seeds a broad Attribute Catalog plus record-type-specific assignments for manual UI coverage. Incoming, Outgoing, Document, Master List Request, Meeting, and Meeting Topic examples exercise text, email, URL, integer, currency, date, date-time, select, multi-select, boolean, and notes controls under named sections. The `v6-dynamic-field-ui-test` migration updates mock assignments without deleting catalog entries or saved record values. Production configuration remains administrator-owned; these demo assignments are not business defaults for the HTTP backend.

## Dynamic workflow stages and record boards

Workflow stages configured on a Record Type are the source of truth for its operational board. This applies to:

- Incoming Document;
- Outgoing Document;
- Document;
- Master List Request;
- any future workflow-enabled record type.

In the Record Type workflow editor, every stage row supports add, edit, delete, initial/final flags, color, and drag-and-drop ordering. Reordering immediately updates the draft stage `order`; saving publishes that same order for runtime consumption.

At runtime, `AppRecordStageBoard` resolves stages for its configured record type instead of using the static `recordWorkflowStages` array as the primary source. The configured stages appear in the left rail in saved order, with counts and search. A user can drag a record card onto a stage row or use **Move to stage** from the row/card action menu. Both interactions call the same transition adapter, enforce configured transitions on the server, refresh affected counts, and roll back/show an error when rejected.

Static frontend stages are fallback-only while configuration cannot be loaded. A configuration load failure must be visible and retryable; the frontend must never silently treat fallback stages as newly published configuration. Disabled/retired stages remain readable for historical records but cannot accept new drops. If a saved URL or record refers to a missing legacy stage, show a safe legacy label and allow navigation without crashing.

Record logs use the same Record Type identity. The log list resolves its Record Type column and category rail from configured record types. Opening **Logs** from a record passes both `entityType` (the stable record-type code) and `entityId`, so the list shows only that record's events. The future HTTP list endpoint must accept these filters and may return `recordTypeId`, `recordTypeCode`, and `recordTypeName`; mock mode follows the same contract.

The record type must have explicit lifecycle actions:

- **Save draft** may store incomplete configuration and never affects runtime records.
- **Publish** validates the complete schema, creates a new immutable schema version, and makes it available to runtime pages.
- **Retire** blocks creation of new records while existing records remain readable and editable according to policy.

Editing a published type creates a draft revision. Existing records retain their values; the UI uses the latest compatible published schema and can display retired fields in a read-only **Legacy fields** section when values still exist.

## Resolved schema contract

`useRecordTypeDrivenTabs` is enabled by entity metadata (`recordBacked: true`), not a hardcoded entity-key set. It resolves by `recordTypeId` when present or the entity's stable `recordTypeCode`, briefly caches the resolved schema, and merges assigned sections into the shared Details tab. Keep this metadata-driven boundary when extracting or renaming the resolver.

The resolver combines:

```text
protected core fields
  + published record-type version
  + type field assignments
  + attribute catalog definitions
  + current-user field permissions
  + page mode (create | detail | edit | list | board | filter)
  = resolved record schema
```

Use a typed shape equivalent to:

```ts
interface ResolvedRecordSchema {
  recordType: { id: string; code: string; name: string; schemaVersion: number }
  tabs: ResolvedRecordTab[]
  fields: ResolvedRecordField[]
  stages: ResolvedStage[]
  capabilities: Record<string, boolean>
  etag?: string
}

interface ResolvedRecordField {
  attributeId: string
  code: string
  label: string
  dataType: AttributeDataType
  tabId: string
  sectionId: string
  order: number
  columnWidth: 1 | 2
  required: boolean
  readOnly: boolean
  visible: boolean
  showOnCreate: boolean
  showOnDetail: boolean
  showInList: boolean
  filterable: boolean
  cardEligible: boolean
  defaultValue?: unknown
  validation?: ValidationRule
  visibility?: VisibilityRule | null
  options?: AttributeOption[]
}
```

Fetch the resolved schema through a typed repository/adapter. Deduplicate requests by record type + schema version + permission context, cache them, support cancellation/stale-response protection, and invalidate the cache after a record type or attribute is published.

## Add, detail, and edit behavior

### Create

1. Resolve or select the record type before rendering type-specific fields.
2. Show core create fields plus assigned fields where `showOnCreate` is true.
3. Apply typed defaults only after the schema loads and only to untouched empty fields.
4. Recompute conditional visibility as dependencies change.
5. If the user changes record type, warn before discarding incompatible entered values. Preserve compatible values by attribute ID/code; do not silently prune them.
6. Submit the selected schema version with the values so stale configuration can be detected.

### Detail

1. Load record identity and its schema version, then resolve the appropriate schema.
2. Render all permitted detail fields in configured tabs/sections, including read-only and legacy values.
3. Lazy-load heavy field controls and option sources when their tab opens.
4. Show a safe unavailable-field placeholder when the user lacks field access; never leak its value in HTML, client state, activity metadata, or exports.

### Edit

1. Use the same schema and value model as detail mode.
2. Disable fields that are read-only, permission-restricted, workflow-locked, or no longer active.
3. Validate visible and hidden required fields according to server-provided rules; conditional fields are required only when their condition applies.
4. Map server field errors by attribute code and focus the first permitted invalid field.
5. Submit only intentional changes or a clearly defined full value map. Never send inaccessible values back as `null`.
6. On `409` schema/version conflict, preserve the user's draft, refetch the schema and record, show what changed, and require an explicit retry.

## Dynamic values and field rendering

At the frontend/API boundary use a JSON-safe value map:

```ts
interface RecordWritePayload {
  recordTypeId: string
  schemaVersion: number
  core: Record<string, unknown>
  attributes: Record<string, unknown> // keyed by stable attribute code
}
```

Keep values typed:

- text/email/phone/URL/reference IDs: string or null;
- integer/decimal/currency: number or null (currency also needs configured currency semantics);
- boolean: boolean or null when tri-state is allowed;
- date/time/datetime: canonical API strings, formatted only for display;
- select/radio: stable option value or null;
- multi-select/checkbox group: array of stable option values;
- file/image: attachment/file reference IDs and metadata, never raw binary in Pinia;
- record/organization/officer/user reference: stable IDs plus separately loaded display summaries.

`AppDynamicFieldRenderer` is the only shared data-type-to-control switch. Unsupported field types render a clear non-destructive error state and telemetry event; they must not crash the entire document form.

## List, board, search, and export behavior

- List column pickers include only permitted assigned fields with `showInList` and a supported cell renderer.
- Dynamic filters come from the resolved list/filter schema and send typed filter operators to the adapter; do not download all records for client filtering.
- Search uses only attributes marked searchable and permitted for the user.
- Board card settings may select assigned fields marked `cardEligible`; title remains a protected core slot.
- When a field is removed or retired, saved user column/card preferences fall back gracefully and surface a small configuration warning.
- Exports use a server-side export request containing record type, schema version, selected field codes, filters, and sort. The server rechecks field permissions.

## Frontend-complete, API-next delivery mode

This phase has a complete frontend/mock flow. The current release defaults `runtimeConfig.public.useMockData` on in every environment so users can exercise configuration and records without backend endpoints. When the backend is ready, set `NUXT_PUBLIC_USE_MOCK_DATA=false`; pages continue through the same typed repositories without rewrites.

- UI components must use typed repositories/composables and must not import mock data directly.
- Mock repositories must remain asynchronous and follow the same request, response, validation, ordering, and error shapes expected from HTTP repositories.
- Dynamic field definitions, record-type assignments, workflow stages, and record `details` values must all pass through this boundary.
- When the backend is ready, implement the documented endpoints behind the existing HTTP repositories and disable mock mode; pages and form components must not require rewrites.
- Backend/API implementation is the next phase and must fit the existing repository contracts rather than changing page components.

## API-ready repository boundary

Components must never invent endpoints. Extend typed repositories/adapters to cover these capabilities, with mock and HTTP implementations sharing the same interface:

```ts
interface RecordSchemaRepository {
  resolve(recordTypeId: string, context: SchemaContext): Promise<ResolvedRecordSchema>
}

interface RecordRepository {
  create(payload: RecordWritePayload): Promise<RecordEnvelope>
  get(id: string): Promise<RecordEnvelope>
  update(id: string, payload: RecordWritePayload, version: string): Promise<RecordEnvelope>
}
```

Expected backend resources remain behind those interfaces:

- attribute catalog CRUD and usage;
- record type draft/publish/version and field assignments;
- resolved runtime schema;
- record CRUD with typed dynamic values;
- server-side list/filter/search/export using dynamic field codes.

Support `ETag`/`If-Match` or an equivalent version token for both configuration publishing and record updates. Treat `422` as field validation, `403` as authoritative permission denial, and `409` as record or schema conflict.

## Permissions and audit

- Separate permissions for catalog management, record-type composition, publishing, and runtime record create/view/edit.
- Support field-level view and edit restrictions in the resolved schema.
- Hiding a field in the UI is not authorization; the API must omit/redact inaccessible definitions and values.
- Audit attribute creation, configuration changes, assignment/layout changes, publishing, retirement, and dynamic value changes.
- Activity UI should show friendly labels while retaining stable codes/version metadata for traceability.

## Failure and loading states

- Do not render an editable type-specific form before its schema is known.
- A schema-loading failure shows retry and safe navigation actions; it must not fall back to an incomplete hardcoded form.
- A missing/retired attribute with existing data renders a read-only legacy field.
- Empty record types show a helpful configured-empty state, not an error.
- Offline/mock mode follows the same lifecycle, schema, validation, and payload contracts so switching to HTTP does not require component rewrites.

## Acceptance criteria

1. An authorized user creates and publishes a catalog attribute without code changes.
2. The user assigns it to Meeting and Document record types with different placement/required overrides.
3. New and existing meeting/document pages render the field on add, detail, and edit from the resolved schema.
4. Values round-trip with correct types and survive refresh, type changes, hidden-field conditions, and schema updates.
5. Eligible dynamic fields can appear in server-backed lists, filters, search, board cards, and exports.
6. A field can be reused by multiple record types without duplication.
7. Published/used fields cannot be destructively changed or deleted; retirement preserves historical display.
8. Permission-restricted fields and values never leak to unauthorized users.
9. Mock and HTTP repositories satisfy the same contract, including schema/version conflicts.
10. Tests cover schema resolution, create/detail/edit parity, type switching, defaults, conditional rules, permission redaction, legacy values, API error mapping, cache invalidation, and inaccessible value preservation.
