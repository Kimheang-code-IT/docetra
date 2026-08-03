# Prompt 25 — Document Type

## Copy/paste prompt

Implement `/configuration/document-types` as document classification configuration. Follow `00-shared-foundation.md` and `00B-configuration-settings-kit.md`.

Use `useConfigurationRepositories().documentTypes`.

### List view

Columns: Name, Code, Direction, Related record type, Default priority, Status, Updated, Actions.

Filters: search, direction, status. Pagination. Actions: Create, Edit, Duplicate, Activate/Deactivate, Delete (confirm).

Routes: `/configuration/document-types`, `/new`, `/:id`.

### Form

- Name, code, description
- Direction: Incoming | Outgoing | Internal | Both
- Related record type (from Record Type repository)
- Default priority, default confidentiality
- Allowed file types, maximum file size
- Active status
- Summary preview before save (`AppSettingCard` or form summary panel)

Referenced types must be disabled rather than hard-deleted. Invalid/duplicate codes surface as field errors.

### Acceptance

Document types drive future document forms; direction and file limits are configurable; mock persistence works across refresh.
