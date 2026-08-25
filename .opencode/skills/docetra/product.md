# Product

## Idea (business intent)

- `prompt/idea/01-docetra-project-brief.md`
- `prompt/idea/02-docetra-business-requirements.md`
- `prompt/idea/03-draft-db-design.md` — column-level draft; prefer `prompt/specification/07-data-model.md` on conflict

## Spec (engineering)

Reading order: `prompt/specification/README.md`

Must-read for most work:

- `00-overview.md`
- `02-domain-model.md`
- `07-data-model.md`
- `modules/record.md`
- `04-permissions-and-access.md`

## Unified record model

Meetings, documents, topics, files, URLs, and similar items are **records** differentiated by `record_type`. Join through `record_type.id` (`record.record_type_id`); `code` is informational and not unique. Types are organization-owned and shareable via `record_type_permission`.

Preferred card/list identity fields: `title`, `status`, `record_stage` / stage, `record_tag` / tags, `record_time`, `record_content`.

Meeting is a special type with topic-container board behavior, not a disconnected entity.

Prefer configuration (record type attributes, stages, card fields) over hardcoded per-screen field lists.

## UI surfaces

`record_type` payload `uiSurface`: `meeting` | `document` | `system`.

Routes:

- `/meetings/{typeCode}` list/board, `/meetings/{typeCode}/new`, `/meetings/{typeCode}/{id}`
- `/records/{typeCode}` same pattern

Do not add a Vue page per type. Catalog comes from `GET /api/v2/records/_meta/surfaces`.

## Conflict order

1. `prompt/specification/`
2. `prompt/idea/` if spec is silent
3. `prompt/frontend/` layout only
4. Existing frontend only for already-shipped mock/UI until migrated
