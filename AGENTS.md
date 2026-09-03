# Docetra — Complete System Integration Mission

This is the single auto-loaded execution document for agents working in this repository. It contains the permanent Docetra rules and the active whole-system completion mission. Read it completely before changing code; execute the work instead of writing another plan.

## Pi GLM execution

Run from the repository root:

```powershell
pi --model zai/glm-5.3-flash --thinking high --name docetra-complete-system --approve "Read AGENTS.md completely. Execute the active Docetra completion mission phase by phase. Preserve unrelated working-tree changes, run every required verification gate, and continue until the acceptance criteria are genuinely satisfied or a real external blocker requires user input."
```

The verified Pi model identifier is `zai/glm-5.3-flash`, and local Pi authentication for this provider is ready.

Agent rules:

- Load the repository `docetra` skill for every feature, bug, integration, performance, or review task.
- Execute phases continuously; do not stop after producing another proposal.
- Preserve every unrelated tracked, deleted, and untracked working-tree change.
- Never reset, clean, overwrite, or revert user-owned work.
- Do not weaken tests, permissions, validation, architecture checks, or error behavior to make checks pass.
- Diagnose and retry ordinary failures autonomously.
- Ask the user only for a genuine external blocker such as missing credentials, destructive external action, unsafe migration ambiguity found in real rows, or an unavailable required service.
- Never commit `backend.env`, `.env`, credentials, tokens, or secrets.
- Never claim success from static inspection. Verify commands, migrations, runtime processes, API contracts, and browser behavior.

## Source of truth

Use this conflict order:

1. `prompt/specification/` for architecture, domain, API, permission, and data rules.
2. `prompt/idea/` when the specification is silent.
3. `prompt/frontend/` for layout/presentation only.
4. Existing shipped behavior until it is migrated.
5. This mission for the explicitly approved integration and ORM-ownership cleanup.

Docetra has one unified `record` domain differentiated by `record_type`. Meeting is a special record type with topic-container behavior, not a separate product domain. Do not create separate document, meeting, file, or URL domains.

Required starting references include `00-overview.md`, `02-domain-model.md`, `04-permissions-and-access.md`, `06-api-contracts.md`, `07-data-model.md`, `modules/record.md`, and the Docetra `connection.md`, `frontend.md`, and `backend.md` skill references.

Permanent frontend rules:

- Pages stay thin. Lists use `WorkspaceEntityWorkspaceView` or the shared stage board; create/show/edit uses `DocumentEntityDocumentView` with `useDocumentPage`; meeting topics use `MeetingAppMeetingTopicBoard`.
- Menus and routes come from active RecordTypes and `uiSurface`; routes remain `/meetings/{typeCode}` and `/records/{typeCode}`.
- All HTTP goes through repositories/adapters and `useApi()`; do not add direct component `$fetch`, `fetch`, Axios, or a second client family.
- New user-facing text requires English and Khmer i18n.
- `AuthUser.permissions` gates presentation only; backend authorization is authoritative.
- Preserve optimistic concurrency through `version` and `If-Match`.
- Do not add a new UI framework, state library, editor, uploader, or chart stack.

Permanent backend rules:

- Routers/application workflows own transactions; services own rules but do not commit; repositories own SQL/flush but no permission/workflow rules.
- PostgreSQL is business and authorization truth. Redis is cache/session only.
- Drive sync, exports, notifications, and scans run through worker/scheduler infrastructure, never inside the API process.
- Significant changes are audited and operational history remains append-oriented.

## Verified starting baseline

Reproduce and save normalized manifests before mutation:

```text
Backend unit/contract: 130 passed, 85 deselected
Architecture: 8 passed
Frontend unit: 67 passed
Frontend typecheck: passed
Frontend production build: passed with large-chunk warnings
import app.main: passed
/api/v2 registered operations: 371
SQLAlchemy tables: 30
Alembic head: 0009_org_record_types
Initial integration score: 62/100
Target score: at least 90/100, supported by evidence
```

Capture `git status --short`, route/OpenAPI manifest, SQLAlchemy metadata manifest, dependency DAG, lazy imports, frontend endpoint usage, login/detail network timelines, and archive/board/dashboard/export request counts.

## Mandatory ORM ownership — remove `backend/app/models`

The former compatibility model package is no longer approved. Completely remove `backend/app/models` after migrating all consumers. Each mapped class has exactly one canonical definition:

```text
app/modules/admin_config/model.py
  Setting, EnumValue, AppSetting

app/modules/organization/model.py
  Organization, OrganizationSector, OrganizationPurpose

app/modules/people_access/model.py
  User, Officer, OfficerIdentifier, Role, Menu, Permission

app/modules/record/model.py
  Record, RecordType, RecordAttribute, RecordTypePermission
  RecordTemplate, RecordStageTemplate, RecordDetail
  RecordAttachment, RecordOrganization, Entity
  Activity, Comment, Favorite, MeetingSchedule

app/modules/storage_integration/model.py
  File

app/platform/audit/model.py
  AuditLog, NotificationAuditLog

app/platform/messaging/model.py
  Outbox
```

Model cleanup requirements:

- Moving definitions must not change table names, columns, constraints, indexes, relationships, mapper behavior, or pre-integration table count.
- `app/db/__init__.py` exports infrastructure only and no mapped class.
- `app/db/metadata.py` is the sole registration aggregator and imports canonical owner modules only to populate `Base.metadata`.
- Alembic imports the metadata registry, never `app.models`.
- Core authentication infrastructure must not import People Access ORM models; current-user dependencies and typed identity access belong in the People Access public dependency/facade.
- Application workflows, jobs, scheduler tasks, integrations, migration scripts, and tests must stop importing `app.models.*` or models through `app.db`.
- Business modules use platform audit/messaging services rather than manipulating another owner table without an explicit platform API.
- Update backend documentation that still identifies `app/models` as canonical.
- Delete the directory only after repository-wide search proves there are no remaining imports.
- Add architecture tests forbidding `app.models`, model exports from `app.db`, sibling model/repository/router/internal-service imports, platform-to-business imports, and metadata drift.
- Do not create an Alembic migration solely for moving Python definitions.

Complete this ORM cleanup as Phase 1, after baseline manifests and before integration behavior changes. Backend and architecture tests must pass before continuing.

## Approved module boundaries

```text
reporting_support → record, organization, people_access, storage_integration
storage_integration → record, admin_config
record → organization, people_access, admin_config
organization → admin_config
people_access → admin_config
admin_config → none
```

Cross-module business imports may use only public `service`, `schema`, and `exceptions` facades. API composition alone imports routers. `app/application/` composes multiple public module services. `core`, `shared`, `integrations`, and `platform` import no business modules. `app/db/metadata.py` is the only model-registration exception and contains no business behavior.

For attachment workflows, use multipart Storage upload followed by an application workflow that validates the public File result and asks Record to create `RecordAttachment`. Record must not import Storage models, repositories, or internal services.

## Approved integration migration

Create one additive migration after `0009_org_record_types`, such as `0010_integration_contract_fields`.

Add `permission.scope` with allowed values `all | creator`, non-null default `all`, and backfill existing rows to `all`.

Add `enum.enum_type`, `label_km`, `color_code`, `ordering`, `is_active`, and `version`. Keep existing `enum.value` as the English label. Replace global `enum.code` uniqueness with unique `(enum_type, code)`. Preserve legacy code/value/description, backfill deterministically, and seed known vocabulary groups idempotently. Do not add a duplicate `label_en` column.

The final table count remains 30. Test upgrade from `0009` using representative existing rows, data preservation, metadata alignment, and downgrade when supported.

## Mandatory Phase 0 connection repair

Before the numbered integration phases below, reproduce and fix `NUXT_E1001`, slow login first paint, request waterfalls, and the `[nostics]: import.meta.hot.send()` warning when project-controlled.

Delayed functions such as `useRecordSurfaces.load()` must not instantiate `useApi()` after Nuxt setup context has ended. Capture Nuxt-dependent clients during setup/plugin/store creation; use `nuxtApp.runWithContext()` only for genuinely delayed work that cannot capture a stable dependency.

Stored user data paints the shell immediately; `/auth/me` validates in the background; refresh occurs only on 401; timeout/5xx does not destroy a valid local session; record GET gates the detail overlay while comments/activity/files/neighbors/favorite/schema overlap or load after paint.

If the `nostics` warning is exclusively dependency/Nuxt DevTools behavior, record its exact source and use a compatible development-only configuration rather than suppressing unrelated warnings.

## Integration mission

Implement the missing and broken frontend ↔ backend API integration identified in the completed integration review.

The backend modular-monolith DAG and public boundaries are already complete and verified. Do not redesign them. The ORM relocation and platform ownership defined above are an explicitly approved cleanup and must preserve that DAG.

Preserve:

* `/api/v2` API prefix
* existing database schema
* Alembic history
* module dependency DAG
* public module boundaries
* existing API/worker/scheduler entry points
* existing frontend working-tree changes unrelated to this task

The approved `0010_integration_contract_fields` additive migration is the only schema/Alembic exception in this mission. Preserve every earlier revision unchanged.

Follow the existing architecture:

```text
Router
→ Application Workflow / Service
→ Repository
→ Database
```

Cross-module communication:

```text
Service
→ Service
```

Do not introduce:

```text
Module A → Module B repository
Module A → Module B model
Module A → Module B internal services
core/shared/integrations → business modules
```

The goal is to make the frontend ↔ backend integration production-complete.

Current integration review score:

```text
62/100
```

Implement fixes in the following order.

# Phase 1 — Fix record and meeting file attachments

This is the highest-priority broken workflow.

Current problem:

The frontend sends multipart file data for meeting attachments, but the current backend attachment endpoint expects JSON metadata.

Document attachments may create local metadata such as:

```text
local-file-*
```

without actually uploading the bytes.

Fix the workflow so an attachment always represents a real uploaded object.

Use the existing storage/file infrastructure where possible.

Preferred flow:

```text
Frontend
   ↓
Upload actual file bytes
   ↓
Backend storage upload endpoint
   ↓
File record / storage object created
   ↓
Attach returned file reference to Record or Meeting
   ↓
Frontend refreshes attachments
```

Do not store fake local-only attachment references.

Reuse the existing working multipart upload flow where appropriate.

Verify:

* upload actual file bytes
* file metadata persistence
* object storage persistence
* attach file to record
* attach file to meeting
* download
* detach the RecordAttachment without deleting a shared File; purge the File/object only when explicitly requested, authorized, and no remaining references exist
* file type validation
* file size validation
* errors
* loading state
* duplicate submit prevention

Do not base64 encode files unless an existing contract explicitly requires it.

# Phase 2 — Add normal file download integration

The backend already supports normal file download but the frontend has no usable workflow.

Add frontend download behavior using the existing API.

Support:

```text
Attachment row
→ Download action
→ API
→ file response
→ browser download
```

Handle:

* filename
* content type
* failed downloads
* authorization errors
* loading state

# Phase 3 — Fix dashboard cache isolation

Current problem:

Dashboard results are permission-filtered but cached globally.

Do not allow data generated for one user or permission set to be served to another user.

Preferred solution:

Either:

1. include user/effective-permission identity in the cache key

or

2. cache only permission-independent data and apply user filtering afterward.

Choose the simplest solution compatible with the current backend.

Add tests proving that:

```text
User A dashboard
≠ incorrectly reused for User B
```

when their permissions differ.

# Phase 4 — Implement vocabulary backend API

The active frontend currently expects:

```text
GET    /api/v2/configuration/enums
POST   /api/v2/configuration/enums/{group}
PATCH  /api/v2/configuration/enums/{group}/{code}
DELETE /api/v2/configuration/enums/{group}/{code}
```

The backend currently does not expose these routes.

Implement these routes using the existing Admin Config `EnumValue` ownership.

Do not move RecordType back into Admin Config.

RecordType remains owned by Record.

Admin Config owns general enum/vocabulary values only.

Provide:

* list vocabulary groups/values
* create value
* update value
* activate/deactivate through `is_active` for RecordType and payload status for RecordAttribute
* delete where safe
* validation
* duplicate-code protection
* stable ordering

Then replace frontend fallback behavior so real API data is the primary source.

Fallback constants may remain only as safe bootstrapping defaults if truly needed.

Do not silently hide API failures.

# Phase 5 — Fix RecordType and RecordAttribute actions

The frontend currently exposes:

```text
duplicate
activate/deactivate
```

but corresponding routes do not exist.

Inspect current product requirements and existing Record service behavior.

If these actions are valid product features, implement the minimum backend operations needed while preserving current API conventions.

Otherwise remove/disable the unsupported frontend action.

Do not leave active buttons that always return 404/405.

Preferred decision rule:

```text
Feature required by existing UI/docs
→ implement backend action

Feature not supported by product requirements
→ remove/disable frontend action
```

Do not invent unnecessary functionality.

# Phase 6 — Complete Google Drive synchronization

Backend already exposes:

```text
POST /portal/google-drive-sync/sources
POST /portal/google-drive-sync/sources/{source_id}/sync
GET  /portal/google-drive-sync/jobs/{job_id}
```

Integrate these into the frontend.

Implement a usable workflow:

```text
Create Drive Source
→ Save source
→ Start Sync
→ receive job_id
→ poll job status
→ show progress/status
→ refresh Drive file list
→ allow linking file to record
```

Support:

* source creation
* source validation
* sync start
* job polling
* completed state
* failed state
* retry failed or cancelled jobs only; never duplicate an active or completed job
* refresh linked files
* useful error messages

Do not create duplicate generic-entity logic if dedicated Drive APIs already exist.

# Phase 7 — Fix permission catalog integration

Current frontend expects a simple:

```text
string[]
```

while backend returns structured permission rows.

The backend structured permission-row catalog is the required canonical contract.

Update frontend types and role matrix to use the real dynamic permission catalog.

Remove hard dependency on static:

```text
ROLE_DOCUMENT_TYPES
```

when the backend already provides the real catalog.

New database-configured RecordTypes must appear automatically where appropriate.

Do not hard-code new RecordTypes into frontend source.

# Phase 8 — Fix creator-only permission enforcement

The UI currently allows:

```text
onlyIfCreator
```

while backend creator-only authorization effectively does not enforce it.

Implement creator-only authorization correctly.

Determine the creator from the canonical resource ownership fields already present in the system.

Required behavior:

```text
Permission without creator restriction
→ normal authorized behavior

Permission with onlyIfCreator
AND current user created the resource
→ allowed

Permission with onlyIfCreator
AND current user did not create the resource
→ forbidden
```

Keep backend authorization authoritative.

Frontend visibility is UX only.

Add authorization tests for:

* creator allowed
* non-creator denied
* privileged/unrestricted behavior if already supported
* record/comment behavior that previously regressed

# Phase 9 — Align audit/log DTO contracts

Current frontend has multiple incompatible log models.

Do not let each page independently guess backend fields.

```text
One canonical Audit DTO
→ frontend adapters for Record/Portal/System views
```

This canonical DTO is the required contract. Extend it compatibly with missing actor/target data when necessary; do not create separate competing backend DTO families for each page.

Create centralized frontend mapping.

Example backend canonical fields:

```text
summary
action
entityType
occurredAt
status
detail
actor
target
```

Then derive UI-specific display fields centrally.

Remove duplicated mapping logic.

Verify:

* dates
* actor
* target/entity
* action
* status
* details
* empty-state behavior

# Phase 10 — Fix server-side pagination, filtering, sorting

Do not allow the frontend to send filters that the backend silently ignores.

Review active list pages one by one:

* records
* organizations
* sectors
* purposes
* users
* officers
* roles
* record types
* record attributes
* uploads
* audit logs

For each page define the exact supported query contract.

Example:

```text
page
page_size
search
status
sort_by
sort_order
date_from
date_to
```

Only support fields that make sense for the resource.

Backend must either:

1. implement the parameter

or

2. frontend must stop sending it.

Do not silently ignore an active UI filter.

Pagination responses should provide real totals.

Avoid:

```text
total = current_page.length
```

unless the endpoint is intentionally unpaginated.

Standardize frontend list metadata where possible:

```text
items
total
page
pageSize
pages
```

Preserve existing external API contracts where required.

If response shape cannot change, normalize it inside frontend adapters.

# Phase 11 — Complete Storage Provider UI

Backend capabilities already exist for additional storage-provider operations.

Add usable frontend flows for:

* create provider
* delete provider
* activate/deactivate provider
* set default provider
* test provider
* edit provider

Keep sensitive credentials protected.

Do not expose stored secrets unnecessarily in API responses.

# Phase 12 — Reduce excessive API requests

Fix the largest frontend/API performance issues without redesigning the system.

## Archive

Current page makes roughly 12 list requests.

Reduce this by using a proper filtered/paginated backend request where possible.

## Stage board

Avoid one request per stage if one backend call can provide the required board dataset.

Do not optimize by loading huge unnecessary datasets.

## Dashboard

Do not refetch identical dashboard data when only client-side chart display changes.

## Export polling

Current polling interval:

```text
1.5 seconds
```

for up to two minutes.

Add reasonable backoff.

Example:

```text
1.5s
→ 2s
→ 3s
→ 5s
```

Stop immediately when:

* completed
* failed
* cancelled
* component/page disposed

# Phase 13 — Semantic Search and Ask AI

Current behavior is placeholder/mock.

Do not pretend these features are real.

No approved AI/semantic provider exists in the current repository scope. Clearly mark these features unavailable/coming later and remove misleading production behavior. Implement them only if repository inspection finds an already-approved working backend capability; do not add a provider.

Do not introduce a new AI provider or external service without explicit project approval.

Do not keep:

```text
semantic mode
```

that behaves identically to keyword search while presenting itself as semantic search.

Do not keep Ask AI returning fake/template intelligence while ignoring selected IDs.

# Phase 14 — Missing lower-priority frontend integrations

After critical workflows work, review:

* export deletion/cancellation
* mentions API
* organization type metadata

Only add them if there is an actual active frontend/product workflow.

Do not create UI simply because an endpoint exists.

# Phase 15 — Remove dead and misleading API usage

Review generic generated routes.

Do not treat every registered backend operation as requiring a frontend feature.

Classify unused routes into:

```text
intentional public/internal contract
legacy compatibility
generated but unused
candidate for later cleanup
```

Do not remove backend routes in this task unless their removal is explicitly safe and approved.

# Frontend API architecture

Keep all network calls centralized.

Preferred structure:

```text
Page / Component
      ↓
Composable / Store
      ↓
Repository / API Adapter
      ↓
useApi()
      ↓
/api/v2
```

Avoid new direct `$fetch`, `fetch`, or Axios calls inside components when the project already has a shared API layer.

Keep API endpoint constants centralized.

# Error handling

Handle:

```text
400
401
403
404
409
422
429
500
```

Rules:

401:
follow existing session-refresh/logout behavior.

403:
show permission error without logging out.

422:
show useful form validation.

409:
show conflict/duplicate message.

429:
show rate-limit feedback.

5xx:
show safe generic failure message.

Never expose raw backend stack traces.

# Loading and mutation state

Every mutation flow should prevent duplicate submission.

For example:

```text
Create
Update
Delete
Upload
Sync
Test provider
Start export
```

Use proper loading states and refresh/cache invalidation after successful mutation.

# Implementation strategy

Do not implement all phases in one huge uncontrolled edit.

Work phase by phase.

After each phase:

1. run relevant backend tests
2. run relevant frontend tests
3. run frontend typecheck
4. verify API contract
5. verify architecture tests
6. continue only if current phase is stable

Do not leave temporary debugging code.

# Required regression verification

Backend:

```text
python -m pytest -q
python -c "import app.main"
```

Run architecture tests separately as well.

Run Compose integration tests when backend behavior changes.

Frontend:

Run the configured:

```text
typecheck
unit tests
build
```

Do not invent commands; inspect package scripts first.

# API contract verification

Compare the final route/OpenAPI manifest against the approved baseline.

Existing contracts should remain unchanged except for explicitly added missing functionality such as vocabulary operations when required by the existing frontend.

Do not accidentally rename or remove unrelated endpoints.

# Database verification

Do not create migrations beyond the explicitly approved additive `0010_integration_contract_fields`. ORM relocation itself creates no migration.

Compare SQLAlchemy metadata with the approved baseline.

Expected baseline:

```text
30 tables
```

# Architecture verification

Existing modular-monolith architecture must remain valid.

Expected architecture dependency tests must continue passing.

Do not weaken tests or add exceptions to make new violations pass.

# End-to-end acceptance tests

Verify manually or through existing E2E capability:

## Auth

```text
Login
→ session restore
→ protected request
→ logout
```

## Record

```text
Create
→ view
→ edit
→ filter/search
→ upload attachment
→ download attachment
→ history/comments
```

## Meeting

```text
Create
→ edit
→ board
→ attachment upload
→ Drive link
```

## Organization

```text
Create
→ edit
→ filter
→ pagination
→ record relationship
```

## Permissions

```text
Role catalog
→ save role
→ restricted user
→ creator-only resource
→ forbidden operation
```

## Configuration

```text
Vocabulary CRUD
→ RecordType/Attribute actions
→ page reload
→ persisted values remain
```

## Storage

```text
Provider create
→ test
→ activate/default
→ upload
→ download
```

## Google Drive

```text
Source create
→ sync
→ job completes
→ files appear
→ file links to record
```

## Reporting

```text
Dashboard
→ different permission users
→ correct isolated result
```

## Audit

```text
Create/update action
→ audit endpoint
→ frontend displays correct actor/action/time/target
```

# Final completion report

When all implementation work is complete, return:

## Final integration score

```text
X/100
```

Target:

```text
90+/100
```

Do not invent a score. Base it on actual integration coverage and verification.

## Fixed

List all completed integration gaps.

## Remaining

List anything intentionally deferred.

## Backend verification

Report actual:

* architecture test result
* unit/contract test result
* Compose integration result
* `import app.main`
* route count
* SQLAlchemy table count

## Frontend verification

Report actual:

* typecheck
* tests
* build

## API compatibility

Report:

* routes added intentionally
* routes removed
* routes changed
* contract mismatches remaining

## Security verification

Confirm:

* dashboard cache isolation
* creator-only enforcement
* 401/403 behavior
* no backend permission weakening

## Performance verification

Report before/after findings for:

* archive request count
* stage board requests
* dashboard refetches
* export polling

## Integration coverage

Report:

* COMPLETE
* PARTIAL
* MISSING
* BROKEN

for:

* Auth
* Records
* Meetings
* Organizations
* People
* Permissions
* Record Configuration
* Vocabularies
* Admin Settings
* Storage
* File Upload/Download
* Google Drive
* Dashboard/Reporting
* Search
* Exports
* Audit Logs

Important:

Do not mark the task complete until tests and actual runtime behavior confirm the integrations work.

Fix real workflows rather than hiding problems with mock data, fallback values, disabled errors, or hard-coded frontend behavior.
