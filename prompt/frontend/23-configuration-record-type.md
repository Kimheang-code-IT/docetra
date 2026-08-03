# Prompt 23 — Record Type

## Copy/paste prompt

Implement `/configuration/record-types` as the control plane for record behavior. Follow `00-shared-foundation.md` and `00B-configuration-settings-kit.md`.

Use `useConfigurationRepositories().recordTypes` (mock repository with localStorage). Do not hardcode mock arrays in the page.

### List view (`/configuration/record-types`)

Server table via `EntityWorkspaceView` or equivalent:

- Columns: Name, Code, Icon, Color, Attribute count, Workflow enabled, Status, Updated, Actions
- Filters: search, active/inactive, workflow enabled
- Sorting, pagination
- Row actions: Edit, Duplicate, Preview, Activate/Deactivate, Delete (confirm)

Create → `/configuration/record-types/new`. Row → `/configuration/record-types/:id`.

### Editor tabs

Use a dedicated editor (not thin `masterDataTabs`):

1. **General** — name, code, description, `AppIconPicker`, `AppColorPicker`, active
2. **Features** — attachments, comments, assignment, sharing, related records, workflow, due date, history, export
3. **Numbering** — prefix, include year, sequence length, reset yearly + `AppNumberingPreview`
4. **Attributes** — assign existing Record Attributes; per-assignment: required, read-only, visible, searchable, filterable, show in list, section, column width, order via `AppSortableList`
5. **Workflow** — `AppWorkflowStageBuilder` (stages + transitions). No diagram builder.
6. **Preview** — `AppRecordFormPreview` updates live when attributes change

Build Record Attribute first. Prefer disable over hard delete when referenced. No casual comments; Configuration Activity optional later.

### Acceptance

Admins can create/edit record types, assign and reorder attributes, configure stages, preview the dynamic form, and retain data across refresh via the mock repository.
