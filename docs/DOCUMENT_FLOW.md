# Docetra — Document Flow

Verified implementation: `config/entities.ts` (incomingDocuments/outgoingDocuments/documents/masterListRequests), `records/{type_code}` engine, `DOCUMENT_WORKFLOW_STAGES` (backend `domain/map.py`).

## Record types

| Type | Route | Numbering | Date key |
|---|---|---|---|
| `incoming_document` | /records/incoming-documents | INC | receivedDate |
| `outgoing_document` | /records/outgoing-documents | OUT | sentDate |
| `document` (combined) | /records/documents | DOC | documentDate |
| `master_list_request` | /records/master-list-requests | MLR | letterDate |

## Default stage flow (documents, 10 stages)

```
created (initial)
  → record_created
  → observation_note
  → waiting_related_document
  → submitted_director → submitted_ddg → submitted_dg
  → further_measures
  → reply
  → finished_final (isFinal)
```

Stage set is a **default** — configurable per record type via the workflow stage builder (Configuration). Transitions via `PATCH /records/{type}/{id}/stage` (action `transition`).

## Incoming document flow

```
Create (INC reference, title, documentType, senderOrganization, receivedDate,
        officeInCharge, involvedOfficers[], externalUnits[], directorGeneralDate,
        directorDate, tags)
  → Tracking (owner, assignee, waiting flag; stage board drag across steps)
  → Attachments (multipart upload / URL / Drive link)
  → Comments & activity on detail page
  → Complete: stage → finished_final
  → Archive (or delete/purge with permissions)
```

- List columns: reference number, title, sender, received date, owner, assignee, waiting, attachment count.
- Filters: `q`, received-date range, waiting (boolean), stage, status; tabs per document type / date.
- "Waiting" marks blocked items (e.g., waiting related document stage).

## Outgoing document flow

Same engine; recipient organization instead of sender, `sentDate` instead of received date. Same stage flow, attachments, comments, archive.

## Combined document view (`document` type)

- Purpose: one list with **all** documents (incoming + outgoing + general) for easy lookup.
- Columns: reference number, title, recordTypeName, documentDate, updatedAt; date-range filter; tabs by documentType/date.
- Backed by the same dynamic record API — no separate domain.

## Master list request

MLR-numbered requests with letter number/subject/date, owner, tags; same lifecycle.

## Common rules

- Create requires title (+ type-specific required fields enforced by record type schema: required attributes from `record_template.is_require`, validated server-side on create/update).
- Dynamic fields: rendered by `AppDynamicFieldRenderer` from `GET /records/{type}/schema`; values persisted in `record_detail` (typed columns).
- Organization links (sender/recipient/office) stored in `record_organization` with role_type; officers in payload fields (participants/involved officers).
- Optimistic concurrency on all edits; stage change requires `transition` permission; comments require `comment`; archive/restore/purge have dedicated actions.
- Everything audited; soft-deleted items recoverable from Archive; purge is permanent and permission-gated.
