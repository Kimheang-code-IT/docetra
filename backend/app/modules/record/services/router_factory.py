"""Thin FastAPI collection router — delegates to CollectionService."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.record.services.creator_scope import authorize_resource
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
from app.core.security import current_user
from app.modules.people_access.dependencies import person
from app.db.session import get_db
from typing import Any as User
from app.modules.record.domain.map import RECORD_RESOURCES
from app.modules.admin_config.service import runtime
import app.modules.record.services.collaboration as collaboration
from app.modules.record.services.service import CollectionService


def router_for(path: str, resource: str, *, service=None) -> APIRouter:
    router = APIRouter(
        prefix=f"/{path}",
        tags=[path.split("/")[0]],
        dependencies=[Depends(authorize_resource(resource, record_resources=RECORD_RESOURCES))],
    )
    service = service or CollectionService(resource)

    @router.get("", response_model=DataEnvelope)
    async def list_items(request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        return await service.list_items(db, user, dict(request.query_params))

    @router.get("/options", response_model=DataEnvelope)
    async def options(request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        listed = await service.list_items(db, user, {**dict(request.query_params), "limit": "200", "status": "active"})
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

    @router.get("/counts", response_model=DataEnvelope)
    async def counts(request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        listed = await service.list_items(db, user, {**dict(request.query_params), "limit": "100", "status": "all"})
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

    @router.post("", response_model=DataEnvelope)
    async def create(request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        content_type = request.headers.get("content-type") or ""
        if content_type.startswith("multipart/form-data"):
            return {"data": await service.create_upload(db, user, request)}
        payload = await request.json()
        return {"data": await service.create(db, user, dict(payload), dict(payload))}

    @router.post("/bulk-delete", response_model=DataEnvelope)
    async def bulk_delete(body: BulkDeleteBody, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        ids = []
        versions = body.versions or {}
        for raw in body.ids[:500]:
            version = versions.get(str(raw))
            token = {"version": version} if version is not None else {}
            await service.soft_delete(db, user, raw, token)
            ids.append(raw)
        return {"data": {"ids": ids}}

    @router.get("/{entity_id}", response_model=DataEnvelope)
    async def get_item(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        return {"data": await service.get_item(db, entity_id, user)}

    @router.patch("/{entity_id}", response_model=DataEnvelope)
    @router.put("/{entity_id}", response_model=DataEnvelope)
    async def update(
        entity_id: str,
        request: Request,
        body: MutationBody,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(current_user),
    ):
        return {"data": await service.update(db, user, entity_id, request_mutation_body(request, body))}

    @router.delete("/{entity_id}", response_model=DataEnvelope)
    async def soft_delete(
        entity_id: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(current_user),
    ):
        return {"data": await service.soft_delete(db, user, entity_id, request_mutation_body(request))}

    @router.delete("/{entity_id}/purge", response_model=DataEnvelope)
    async def purge(
        entity_id: str,
        request: Request,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(current_user),
    ):
        return {"data": await service.purge(db, user, entity_id, request_mutation_body(request))}

    @router.post("/{entity_id}/archive", response_model=DataEnvelope)
    async def archive(
        entity_id: str,
        request: Request,
        body: MutationBody | None = None,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(current_user),
    ):
        return {"data": await service.lifecycle(db, user, entity_id, "archived", request_mutation_body(request, body))}

    @router.post("/{entity_id}/restore", response_model=DataEnvelope)
    async def restore(
        entity_id: str,
        request: Request,
        body: MutationBody | None = None,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(current_user),
    ):
        return {"data": await service.lifecycle(db, user, entity_id, "active", request_mutation_body(request, body))}

    @router.patch("/{entity_id}/stage", response_model=DataEnvelope)
    async def stage(
        entity_id: str,
        request: Request,
        body: StageBody,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(current_user),
    ):
        payload = request_mutation_body(request, body)
        return {"data": await service.set_stage(db, user, entity_id, payload.get("stage"), payload)}

    @router.get("/{entity_id}/neighbors", response_model=DataEnvelope)
    async def neighbors(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await service.get_item(db, entity_id, user)
        return {"data": await collaboration.get_neighbors(db, resource, entity_id)}

    @router.get("/{entity_id}/favorite", response_model=DataEnvelope)
    async def get_favorite(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await service.get_item(db, entity_id, user)
        return {"data": {"isFavorite": await collaboration.get_favorite(db, user.id, entity_id)}}

    @router.put("/{entity_id}/favorite", response_model=DataEnvelope)
    async def set_favorite(
        entity_id: str,
        body: FavoriteBody,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(current_user),
    ):
        await service.get_item(db, entity_id, user)
        desired = bool(body.isFavorite)
        await collaboration.set_favorite(db, user.id, entity_id, desired)
        await db.flush()
        return {"data": {"isFavorite": desired}}

    @router.get("/{entity_id}/comments", response_model=DataEnvelope)
    async def comments(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await service.get_item(db, entity_id, user)
        data, total = await collaboration.list_comments(db, resource, entity_id, user)
        return {"data": data, "meta": {"page": 1, "limit": total or 20, "total": total}}

    @router.post("/{entity_id}/comments", response_model=DataEnvelope)
    async def add_comment(
        entity_id: str,
        body: CommentBody,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(current_user),
    ):
        from app.core.errors import DomainError
        general = runtime.general_defaults(await runtime.load_app_config(db))
        if not general["enableComments"]:
            raise DomainError("COMMENTS_DISABLED", "Comments are disabled in application settings", 403)
        await service.get_item(db, entity_id, user)
        comment = await collaboration.add_comment(db, uuid.UUID(entity_id), body.body, user)
        await db.flush()
        await db.refresh(comment)
        return {"data": {"id": str(comment.id), "entityType": resource, "entityId": entity_id, "body": comment.body, "author": person(user), "createdAt": iso_utc(comment.created_at)}}

    @router.patch("/{entity_id}/comments/{comment_id}", response_model=DataEnvelope)
    async def edit_comment(
        entity_id: str,
        comment_id: str,
        body: CommentBody,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(current_user),
    ):
        await service.get_item(db, entity_id, user)
        data = await collaboration.edit_comment(db, entity_id, comment_id, body.body, user)
        await db.flush()
        return {"data": {**data, "entityType": resource}}

    @router.delete("/{entity_id}/comments/{comment_id}", response_model=DataEnvelope)
    async def delete_comment(entity_id: str, comment_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await service.get_item(db, entity_id, user)
        comment_id = await collaboration.delete_comment(db, entity_id, comment_id, user)
        await db.flush()
        return {"data": {"id": comment_id}}

    @router.get("/{entity_id}/activity", response_model=DataEnvelope)
    async def activity(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await service.get_item(db, entity_id, user)
        data, total = await collaboration.list_activity(db, resource, entity_id, user)
        return {"data": data, "meta": {"page": 1, "limit": total or 20, "total": total}}

    @router.get("/{entity_id}/attachments", response_model=DataEnvelope)
    async def attachments(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        payload = await service.get_item(db, entity_id, user)
        return {"data": payload.get("attachments", [])}

    @router.put("/{entity_id}/attachments", response_model=DataEnvelope)
    @router.post("/{entity_id}/attachments", response_model=DataEnvelope)
    async def replace_attachments(
        entity_id: str,
        request: Request,
        body: AttachmentsBody,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(current_user),
    ):
        payload = request_mutation_body(request, body)
        files = payload.get("files") or payload.get("attachments") or []
        await service.update(db, user, entity_id, {"attachments": files, "version": payload.get("version")})
        return {"data": files}

    return router
