"""Dynamic `/api/v2/records/{type_code}` collections + surfaces meta."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import authorize_type_code
from app.core.datetime import iso_utc
from app.core.http_schemas import (
    AttachmentsBody,
    BulkDeleteBody,
    CommentBody,
    DataEnvelope,
    FavoriteBody,
    MutationBody,
    StageBody,
)
from app.core.mutations import request_mutation_body
from app.core.privileged import is_unrestricted
from app.core.security import current_user, person
from app.db.session import get_db
from app.models.people import User
from app.models.record import RecordType
import app.modules.record.services.collaboration as collaboration
from app.modules.record.domain.map import (
    TYPE_CODE_TO_RESOURCE,
    is_valid_type_code,
    merge_type_ui_payload,
)
from app.modules.record.domain.schemas import MeetingAssignTopic, MeetingLinkDrive, MeetingReorder, RecordPayload
from app.modules.record.services.service import CollectionService
import app.modules.record.services.serializer as record_ser

router = APIRouter(tags=["records"])


@router.get("/records/_meta/surfaces", response_model=DataEnvelope)
async def record_surfaces(db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    import app.modules.record.services.type_access as type_access
    from app.core.privileged import is_unrestricted

    stmt = select(RecordType).where(RecordType.is_active == 1).order_by(RecordType.code)
    if not is_unrestricted(user):
        org_id = await type_access.actor_organization_id(db, user)
        type_ids = await type_access.permitted_type_ids(db, org_id)
        if not type_ids:
            return {"data": {"meeting": [], "document": [], "system": []}}
        stmt = stmt.where(RecordType.id.in_(type_ids))
    rows = (await db.scalars(stmt)).all()
    grouped: dict[str, list] = {"meeting": [], "document": [], "system": []}
    for row in rows:
        payload = merge_type_ui_payload(row.code, dict(row.payload or {}))
        surface = str(payload.get("uiSurface") or "document")
        if surface not in grouped:
            grouped[surface] = []
        item = {
            "id": str(row.id),
            "code": row.code,
            "name": row.nam or row.code,
            "description": row.description,
            **payload,
            "apiBase": f"/api/v2/records/{row.code}",
            "routeBase": (
                f"/meetings/{payload.get('slug') or row.code}"
                if surface == "meeting"
                else f"/records/{payload.get('slug') or row.code}"
            ),
        }
        grouped[surface].append(item)
    for key in grouped:
        grouped[key].sort(key=lambda x: (int(x.get("menuOrder") or 100), str(x.get("name") or "")))
    return {"data": grouped}


@router.get("/records/logs", response_model=DataEnvelope)
async def document_surface_logs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    """Activity across document-surface record types (legacy record-logs replacement)."""
    from app.core.authorization import require_permission

    if not is_unrestricted(user):
        require_permission(user, "records.logs.view")
    service = CollectionService("record-logs")
    return await service.list_items(db, user, dict(request.query_params))


def _service(type_code: str) -> CollectionService:
    if not is_valid_type_code(type_code):
        raise HTTPException(404, "Record type not found")
    return CollectionService(type_code=type_code)


def _collab_resource(type_code: str) -> str:
    return TYPE_CODE_TO_RESOURCE.get(type_code) or type_code


@router.get("/records/{type_code}/schema", response_model=DataEnvelope, dependencies=[Depends(authorize_type_code())])
async def record_type_schema(type_code: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    if not is_valid_type_code(type_code):
        raise HTTPException(404, "Record type not found")
    import app.modules.record.services.type_access as type_access
    from app.core.privileged import is_unrestricted

    rtype = await record_ser.resolve_or_ensure_type(
        db,
        type_code,
        None,
        await type_access.actor_organization_id(db, user),
        unrestricted=is_unrestricted(user),
    )
    await type_access.require_type_access(db, rtype, user)
    await db.commit()
    await db.refresh(rtype)
    ui = merge_type_ui_payload(rtype.code, dict(rtype.payload or {}))
    return {
        "data": {
            "recordType": {
                "id": str(rtype.id),
                "code": rtype.code,
                "name": rtype.nam or rtype.code,
                "schemaVersion": 1,
                **ui,
            },
            "coreFields": ["title", "status", "stage", "recordTime"],
            "attributes": [],
            "sections": [],
        }
    }


# Dynamic collection routes — registered after static `_meta` / `logs` paths.
type_router = APIRouter(prefix="/records/{type_code}", dependencies=[Depends(authorize_type_code())])


@type_router.get("", response_model=DataEnvelope)
async def list_items(type_code: str, request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await _service(type_code).list_items(db, user, dict(request.query_params))


@type_router.get("/options", response_model=DataEnvelope)
async def options(type_code: str, request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    listed = await _service(type_code).list_items(db, user, {**dict(request.query_params), "limit": "200", "status": "active"})
    q = (request.query_params.get("q") or "").lower()
    value_field = request.query_params.get("valueField") or "id"
    items = []
    for payload in listed["data"]:
        label = str(payload.get("name") or payload.get("title") or payload.get("code") or payload.get("id"))
        if q and q not in label.lower():
            continue
        items.append({
            "id": str(payload["id"]),
            "label": label,
            "value": str(payload.get(value_field, payload["id"])),
            "parentId": payload.get("parentId"),
            "meta": {"id": str(payload["id"]), "name": payload.get("name") or label, "code": payload.get("code")},
        })
    return {"data": items[: min(200, int(request.query_params.get("limit") or 100))]}


@type_router.get("/counts", response_model=DataEnvelope)
async def counts(type_code: str, request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    listed = await _service(type_code).list_items(db, user, {**dict(request.query_params), "limit": "100", "status": "all"})
    group = request.query_params.get("groupBy") or "stage"
    groups: dict[str, int] = {}
    unassigned = 0
    for item in listed["data"]:
        value = item.get(group)
        if value in {None, ""}:
            unassigned += 1
        else:
            groups[str(value)] = groups.get(str(value), 0) + 1
    return {"data": {"total": len(listed["data"]), "unassigned": unassigned, "groups": groups}}


@type_router.post("", response_model=DataEnvelope)
async def create(type_code: str, request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    service = _service(type_code)
    content_type = request.headers.get("content-type") or ""
    if content_type.startswith("multipart/form-data"):
        return {"data": await service.create_upload(db, user, request)}
    payload = await request.json()
    return {"data": await service.create(db, user, dict(payload), dict(payload))}


@type_router.post("/bulk-delete", response_model=DataEnvelope)
async def bulk_delete(type_code: str, body: BulkDeleteBody, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    service = _service(type_code)
    ids = []
    versions = body.versions or {}
    for raw in body.ids[:500]:
        version = versions.get(str(raw))
        token = {"version": version} if version is not None else {}
        await service.soft_delete(db, user, raw, token)
        ids.append(raw)
    return {"data": {"ids": ids}}


@type_router.post("/reorder", response_model=DataEnvelope)
async def reorder_meetings(type_code: str, body: MeetingReorder, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    from app.core.authorization import require_permission
    import app.modules.record.services.meeting as meeting_board

    if type_code != "meeting_history":
        raise HTTPException(404, "Not found")
    require_permission(user, "records.meeting_history.edit")
    return {"data": await meeting_board.reorder_meetings(db, body.model_dump(exclude_unset=True))}


@type_router.get("/{entity_id}", response_model=DataEnvelope)
async def get_item(type_code: str, entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return {"data": await _service(type_code).get_item(db, entity_id, user)}


@type_router.patch("/{entity_id}", response_model=DataEnvelope)
@type_router.put("/{entity_id}", response_model=DataEnvelope)
async def update(
    type_code: str,
    entity_id: str,
    request: Request,
    body: RecordPayload,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {"data": await _service(type_code).update(db, user, entity_id, request_mutation_body(request, body))}


@type_router.delete("/{entity_id}", response_model=DataEnvelope)
async def soft_delete(
    type_code: str,
    entity_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {"data": await _service(type_code).soft_delete(db, user, entity_id, request_mutation_body(request))}


@type_router.delete("/{entity_id}/purge", response_model=DataEnvelope)
async def purge(
    type_code: str,
    entity_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {"data": await _service(type_code).purge(db, user, entity_id, request_mutation_body(request))}


@type_router.post("/{entity_id}/archive", response_model=DataEnvelope)
async def archive(
    type_code: str,
    entity_id: str,
    request: Request,
    body: MutationBody | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {"data": await _service(type_code).lifecycle(db, user, entity_id, "archived", request_mutation_body(request, body))}


@type_router.post("/{entity_id}/restore", response_model=DataEnvelope)
async def restore(
    type_code: str,
    entity_id: str,
    request: Request,
    body: MutationBody | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {"data": await _service(type_code).lifecycle(db, user, entity_id, "active", request_mutation_body(request, body))}


@type_router.patch("/{entity_id}/stage", response_model=DataEnvelope)
async def stage(
    type_code: str,
    entity_id: str,
    request: Request,
    body: StageBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    payload = request_mutation_body(request, body)
    return {"data": await _service(type_code).set_stage(db, user, entity_id, payload.get("stage"), payload)}


@type_router.get("/{entity_id}/neighbors", response_model=DataEnvelope)
async def neighbors(type_code: str, entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    await _service(type_code).get_item(db, entity_id, user)
    return {"data": await collaboration.get_neighbors(db, _collab_resource(type_code), entity_id)}


@type_router.get("/{entity_id}/favorite", response_model=DataEnvelope)
async def get_favorite(type_code: str, entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    await _service(type_code).get_item(db, entity_id, user)
    return {"data": {"isFavorite": await collaboration.get_favorite(db, user.id, entity_id)}}


@type_router.put("/{entity_id}/favorite", response_model=DataEnvelope)
async def set_favorite(type_code: str, entity_id: str, body: FavoriteBody, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    await _service(type_code).get_item(db, entity_id, user)
    desired = bool(body.isFavorite)
    await collaboration.set_favorite(db, user.id, entity_id, desired)
    await db.commit()
    return {"data": {"isFavorite": desired}}


@type_router.get("/{entity_id}/comments", response_model=DataEnvelope)
async def comments(type_code: str, entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    await _service(type_code).get_item(db, entity_id, user)
    data, total = await collaboration.list_comments(db, _collab_resource(type_code), entity_id, user)
    return {"data": data, "meta": {"page": 1, "limit": total or 20, "total": total}}


@type_router.post("/{entity_id}/comments", response_model=DataEnvelope)
async def add_comment(type_code: str, entity_id: str, body: CommentBody, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    from app.core.errors import DomainError
    import app.modules.admin_config.services.runtime as runtime

    general = runtime.general_defaults(await runtime.load_app_config(db))
    if not general["enableComments"]:
        raise DomainError("COMMENTS_DISABLED", "Comments are disabled in application settings", 403)
    await _service(type_code).get_item(db, entity_id, user)
    comment = await collaboration.add_comment(db, uuid.UUID(entity_id), body.body, user)
    await db.commit()
    await db.refresh(comment)
    resource = _collab_resource(type_code)
    return {
        "data": {
            "id": str(comment.id),
            "entityType": resource,
            "entityId": entity_id,
            "body": comment.body,
            "author": person(user),
            "createdAt": iso_utc(comment.created_at),
        }
    }


@type_router.patch("/{entity_id}/comments/{comment_id}", response_model=DataEnvelope)
async def edit_comment(
    type_code: str,
    entity_id: str,
    comment_id: str,
    body: CommentBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await _service(type_code).get_item(db, entity_id, user)
    resource = _collab_resource(type_code)
    data = await collaboration.edit_comment(db, entity_id, comment_id, body.body, user)
    await db.commit()
    return {"data": {**data, "entityType": resource}}


@type_router.delete("/{entity_id}/comments/{comment_id}", response_model=DataEnvelope)
async def delete_comment(
    type_code: str,
    entity_id: str,
    comment_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    await _service(type_code).get_item(db, entity_id, user)
    deleted_id = await collaboration.delete_comment(db, entity_id, comment_id, user)
    await db.commit()
    return {"data": {"id": deleted_id}}


@type_router.get("/{entity_id}/activity", response_model=DataEnvelope)
async def activity(type_code: str, entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    await _service(type_code).get_item(db, entity_id, user)
    data, total = await collaboration.list_activity(db, _collab_resource(type_code), entity_id, user)
    return {"data": data, "meta": {"page": 1, "limit": total or 20, "total": total}}


@type_router.get("/{entity_id}/attachments", response_model=DataEnvelope)
async def attachments(type_code: str, entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    payload = await _service(type_code).get_item(db, entity_id, user)
    return {"data": payload.get("attachments", [])}


@type_router.put("/{entity_id}/attachments", response_model=DataEnvelope)
@type_router.post("/{entity_id}/attachments", response_model=DataEnvelope)
async def replace_attachments(
    type_code: str,
    entity_id: str,
    request: Request,
    body: AttachmentsBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    payload = request_mutation_body(request, body)
    files = payload.get("files") or payload.get("attachments") or []
    await _service(type_code).update(db, user, entity_id, {"attachments": files, "version": payload.get("version")})
    return {"data": files}


@type_router.post("/{entity_id}/assign-topic", response_model=DataEnvelope)
async def assign_topic(
    type_code: str,
    entity_id: str,
    body: MeetingAssignTopic,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    from app.core.authorization import require_permission
    import app.modules.record.services.meeting as meeting_board

    if type_code != "meeting_history":
        raise HTTPException(404, "Not found")
    require_permission(user, "records.meeting_history.assign")
    return {"data": await meeting_board.assign_topic(db, entity_id, body.model_dump(exclude_unset=True))}


@type_router.post("/{entity_id}/attachments/link", response_model=DataEnvelope)
async def link_drive_attachment(
    type_code: str,
    entity_id: str,
    body: MeetingLinkDrive,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    from app.core.authorization import require_permission
    import app.modules.record.services.meeting as meeting_board

    if type_code != "meeting_history":
        raise HTTPException(404, "Not found")
    require_permission(user, "records.meeting_history.edit")
    return {"data": await meeting_board.link_drive_attachment(db, entity_id, body.model_dump(exclude_unset=True))}


router.include_router(type_router)
