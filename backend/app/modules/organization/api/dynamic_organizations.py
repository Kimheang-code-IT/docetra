"""Dynamic `/api/v2/organizations/{org_type}` collections + meta."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import authorize_org_type
from app.core.datetime import iso_utc
from app.core.http_schemas import (
    AttachmentsBody,
    BulkDeleteBody,
    CommentBody,
    DataEnvelope,
    FavoriteBody,
    MutationBody,
)
from app.core.mutations import request_mutation_body
from app.core.security import current_user, person
from app.db.session import get_db
from app.models.people import User
import app.modules.record.services.collaboration as collaboration
from app.modules.organization.domain.map import ORG_TYPE_META, ORG_TYPE_TO_RESOURCE, is_valid_org_type, permission_prefix_for_org_type
from app.modules.organization.domain.schemas import OrganizationPayload
from app.modules.record.services.service import CollectionService

router = APIRouter(tags=["organizations"])


@router.get("/organizations/_meta/types", response_model=DataEnvelope)
async def organization_types(user: User = Depends(current_user)):
    items = []
    for org_type, meta in ORG_TYPE_META.items():
        items.append({
            "code": org_type,
            **meta,
            "permissionPrefix": permission_prefix_for_org_type(org_type),
        })
    items.sort(key=lambda x: int(x.get("menuOrder") or 100))
    return {"data": items}


def _service(org_type: str) -> CollectionService:
    if not is_valid_org_type(org_type):
        raise HTTPException(404, "Organization type not found")
    return CollectionService(org_type=org_type)


def _collab_resource(org_type: str) -> str:
    return ORG_TYPE_TO_RESOURCE.get(org_type) or org_type


type_router = APIRouter(prefix="/organizations/{org_type}", dependencies=[Depends(authorize_org_type())])


@type_router.get("", response_model=DataEnvelope)
async def list_items(org_type: str, request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return await _service(org_type).list_items(db, user, dict(request.query_params))


@type_router.get("/options", response_model=DataEnvelope)
async def options(org_type: str, request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    listed = await _service(org_type).list_items(db, user, {**dict(request.query_params), "limit": "200", "status": "active"})
    q = (request.query_params.get("q") or "").lower()
    value_field = request.query_params.get("valueField") or "id"
    items = []
    for payload in listed["data"]:
        label = str(payload.get("name") or payload.get("code") or payload.get("id"))
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
async def counts(org_type: str, request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    listed = await _service(org_type).list_items(db, user, {**dict(request.query_params), "limit": "100", "status": "all"})
    group = request.query_params.get("groupBy") or "parentId"
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
async def create(org_type: str, body: OrganizationPayload, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    payload = body.model_dump(exclude_unset=True)
    return {"data": await _service(org_type).create(db, user, dict(payload), dict(payload))}


@type_router.post("/bulk-delete", response_model=DataEnvelope)
async def bulk_delete(org_type: str, body: BulkDeleteBody, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    service = _service(org_type)
    ids = []
    versions = body.versions or {}
    for raw in body.ids[:500]:
        version = versions.get(str(raw))
        token = {"version": version} if version is not None else {}
        await service.soft_delete(db, user, raw, token)
        ids.append(raw)
    return {"data": {"ids": ids}}


@type_router.get("/{entity_id}", response_model=DataEnvelope)
async def get_item(org_type: str, entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    return {"data": await _service(org_type).get_item(db, entity_id)}


@type_router.patch("/{entity_id}", response_model=DataEnvelope)
@type_router.put("/{entity_id}", response_model=DataEnvelope)
async def update(
    org_type: str,
    entity_id: str,
    request: Request,
    body: OrganizationPayload,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {"data": await _service(org_type).update(db, user, entity_id, request_mutation_body(request, body))}


@type_router.delete("/{entity_id}", response_model=DataEnvelope)
async def soft_delete(
    org_type: str,
    entity_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {"data": await _service(org_type).soft_delete(db, user, entity_id, request_mutation_body(request))}


@type_router.delete("/{entity_id}/purge", response_model=DataEnvelope)
async def purge(
    org_type: str,
    entity_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {"data": await _service(org_type).purge(db, user, entity_id, request_mutation_body(request))}


@type_router.post("/{entity_id}/archive", response_model=DataEnvelope)
async def archive(
    org_type: str,
    entity_id: str,
    request: Request,
    body: MutationBody | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {"data": await _service(org_type).lifecycle(db, user, entity_id, "archived", request_mutation_body(request, body))}


@type_router.post("/{entity_id}/restore", response_model=DataEnvelope)
async def restore(
    org_type: str,
    entity_id: str,
    request: Request,
    body: MutationBody | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    return {"data": await _service(org_type).lifecycle(db, user, entity_id, "active", request_mutation_body(request, body))}


@type_router.get("/{entity_id}/neighbors", response_model=DataEnvelope)
async def neighbors(org_type: str, entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    await _service(org_type).get_item(db, entity_id)
    return {"data": await collaboration.get_neighbors(db, _collab_resource(org_type), entity_id)}


@type_router.get("/{entity_id}/favorite", response_model=DataEnvelope)
async def get_favorite(org_type: str, entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    await _service(org_type).get_item(db, entity_id)
    return {"data": {"isFavorite": await collaboration.get_favorite(db, user.id, entity_id)}}


@type_router.put("/{entity_id}/favorite", response_model=DataEnvelope)
async def set_favorite(org_type: str, entity_id: str, body: FavoriteBody, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    await _service(org_type).get_item(db, entity_id)
    desired = bool(body.isFavorite)
    await collaboration.set_favorite(db, user.id, entity_id, desired)
    await db.commit()
    return {"data": {"isFavorite": desired}}


@type_router.get("/{entity_id}/comments", response_model=DataEnvelope)
async def comments(org_type: str, entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    await _service(org_type).get_item(db, entity_id)
    data, total = await collaboration.list_comments(db, _collab_resource(org_type), entity_id, user)
    return {"data": data, "meta": {"page": 1, "limit": total or 20, "total": total}}


@type_router.post("/{entity_id}/comments", response_model=DataEnvelope)
async def add_comment(org_type: str, entity_id: str, body: CommentBody, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    from app.core.errors import DomainError
    import app.modules.admin_config.services.runtime as runtime

    general = runtime.general_defaults(await runtime.load_app_config(db))
    if not general["enableComments"]:
        raise DomainError("COMMENTS_DISABLED", "Comments are disabled in application settings", 403)
    await _service(org_type).get_item(db, entity_id)
    comment = await collaboration.add_comment(db, uuid.UUID(entity_id), body.body, user)
    await db.commit()
    await db.refresh(comment)
    resource = _collab_resource(org_type)
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
    org_type: str,
    entity_id: str,
    comment_id: str,
    body: CommentBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    resource = _collab_resource(org_type)
    data = await collaboration.edit_comment(db, entity_id, comment_id, body.body, user)
    await db.commit()
    return {"data": {**data, "entityType": resource}}


@type_router.delete("/{entity_id}/comments/{comment_id}", response_model=DataEnvelope)
async def delete_comment(
    org_type: str,
    entity_id: str,
    comment_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    deleted_id = await collaboration.delete_comment(db, entity_id, comment_id)
    await db.commit()
    return {"data": {"id": deleted_id}}


@type_router.get("/{entity_id}/activity", response_model=DataEnvelope)
async def activity(org_type: str, entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    data, total = await collaboration.list_activity(db, _collab_resource(org_type), entity_id, user)
    return {"data": data, "meta": {"page": 1, "limit": total or 20, "total": total}}


@type_router.get("/{entity_id}/attachments", response_model=DataEnvelope)
async def attachments(org_type: str, entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
    payload = await _service(org_type).get_item(db, entity_id)
    return {"data": payload.get("attachments", [])}


@type_router.put("/{entity_id}/attachments", response_model=DataEnvelope)
@type_router.post("/{entity_id}/attachments", response_model=DataEnvelope)
async def replace_attachments(
    org_type: str,
    entity_id: str,
    request: Request,
    body: AttachmentsBody,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    payload = request_mutation_body(request, body)
    files = payload.get("files") or payload.get("attachments") or []
    await _service(org_type).update(db, user, entity_id, {"attachments": files, "version": payload.get("version")})
    return {"data": files}


router.include_router(type_router)
