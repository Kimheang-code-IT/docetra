# Document collaboration API contract

The shared entity adapter is the only boundary between document UI components and backend APIs. UI components must not construct URLs, persist favorites, or scan entity lists.

## Response envelope

All endpoints return the existing application envelope:

```json
{
  "data": {},
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 0,
    "totalPages": 1,
    "nextCursor": null
  },
  "errors": []
}
```

`meta` is required for collections and optional for single resources. For large comment/activity feeds, cursor pagination is preferred; page pagination remains supported by the current client.

## Comments

Given an entity collection endpoint such as `/api/v2/records/documents`:

- `GET /:entityId/comments?page=1&limit=20` lists comments newest first.
- `POST /:entityId/comments` with `{ "body": "..." }` creates a comment for the authenticated user.
- `PATCH /:entityId/comments/:commentId` with `{ "body": "..." }` edits a comment.
- `DELETE /:entityId/comments/:commentId` deletes a comment.

The server derives the author from the auth token. It must enforce that only the comment author or an explicitly privileged role can edit/delete. Update responses return the full comment including `editedAt`.

## Record neighbors

`GET /:entityId/neighbors?sort=-updatedAt` returns:

```json
{
  "data": {
    "previousId": "record-101",
    "nextId": "record-099"
  }
}
```

This endpoint prevents the browser from downloading or scanning entity pages. Use a stable compound order such as `(updated_at DESC, id DESC)` and index it. Apply the same authorization scope used by the entity list so inaccessible records are never returned.

## Per-user favorites

- `GET /:entityId/favorite` returns `{ "data": { "isFavorite": true } }`.
- `PUT /:entityId/favorite` with `{ "isFavorite": true }` adds or removes the authenticated user's favorite.

The server derives the user from the auth token. A suitable unique constraint is `(user_id, entity_type, entity_id)`. The PUT operation should be idempotent.

## Performance and correctness

- Keep comment and activity responses bounded; never return the full history by default.
- Add indexes for comment `(entity_type, entity_id, created_at DESC, id DESC)` and favorites `(user_id, entity_type, entity_id)`.
- Return `404` for missing/inaccessible entities and `403` for unauthorized mutations according to the project's security policy.
- Validate trimmed, non-empty comment bodies and enforce a server-side maximum length.
- Prefer an entity `version` or `updatedAt` precondition for concurrent document edits.
- Keep all mutation responses authoritative so the client can replace optimistic state with server state.
