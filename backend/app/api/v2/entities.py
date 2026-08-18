import math
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.datastructures import UploadFile as StarletteUploadFile
from sqlalchemy import String, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.authorization import authorize_resource, creator_only
from app.core.config import settings
from app.core.datetime import extract_record_time, iso_utc, parse_instant, utcnow
from app.core.security import current_user, person
from app.db import Activity, AppSetting, Comment, Entity, Favorite, Outbox, User, get_db
from app.modules.identity import normalize_identity_payload, strip_secrets, sync_login_user, refresh_role_users
from app.modules.identity.sync import sync_domain_row
from app.modules.record.validation import validate_department_parent, validate_record_payload
from app.modules.storage_integration.storage import delete_object, put_bytes, safe_name
from app.modules.storage_integration.upload_validation import detect_upload_type

RESOURCE_PATHS = {
    "meetings/topics": "meeting-topics",
    "meetings/history": "meeting-history",
    "records/incoming-documents": "incoming-documents",
    "records/outgoing-documents": "outgoing-documents",
    "records/documents": "documents",
    "records/master-list-requests": "master-list-requests",
    "records/logs": "record-logs",
    "organizations/departments": "departments",
    "organizations/companies": "companies",
    "organizations/company-purposes": "company-purposes",
    "organizations/company-sectors": "company-sectors",
    "organizations/officers": "officers",
    "users/roles": "roles",
    "users": "users",
    "configuration/record-types": "record-types",
    "configuration/record-attributes": "record-attributes",
    "portal/file-uploads": "file-uploads",
    "portal/google-drive-sync": "google-drive-sync",
    "portal/logs": "portal-logs",
    "system/logs": "system-logs",
}
READ_ONLY = {"record-logs", "portal-logs", "system-logs"}
DOMAIN_STATUS = {"file-uploads", "export-jobs", "google-drive-sync"}
QUERY_KEYS = {"q", "search", "page", "limit", "sort", "view", "status", "stage", "startDate", "endDate", "groupBy"}


def stamp(entity: Entity) -> dict[str, Any]:
    result = dict(entity.payload or {})
    result.update({
        "id": str(entity.id),
        "createdAt": iso_utc(entity.created_at),
        "updatedAt": iso_utc(entity.updated_at),
        "version": entity.version,
    })
    if entity.stage is not None:
        result["stage"] = entity.stage
    if entity.archived_at:
        result["archivedAt"] = iso_utc(entity.archived_at)
    if entity.deleted_at:
        result["deletedAt"] = iso_utc(entity.deleted_at)
    if entity.record_time:
        result.setdefault("recordTime", iso_utc(entity.record_time))
    if entity.status in {"archived", "deleted"} or entity.resource not in DOMAIN_STATUS:
        result["status"] = entity.status
    elif "status" not in result:
        result["status"] = entity.status
    return strip_secrets(result)


async def entity_or_404(db: AsyncSession, resource: str, entity_id: str) -> Entity:
    try:
        uid = uuid.UUID(entity_id)
    except ValueError as exc:
        raise HTTPException(404, "Not found") from exc
    row = await db.scalar(select(Entity).where(Entity.id == uid, Entity.resource == resource))
    if not row:
        raise HTTPException(404, "Not found")
    return row


async def audit(db: AsyncSession, entity: Entity, user: User, action: str, summary: str) -> None:
    db.add(Activity(entity_id=entity.id, actor_id=user.id, action=action, summary=summary))
    db.add(Outbox(topic=f"entity.{action}", payload={"resource": entity.resource, "id": str(entity.id)}))
    if entity.resource not in READ_ONLY:
        title = (entity.payload or {}).get("title") or (entity.payload or {}).get("name") or str(entity.id)
        db.add(Entity(
            resource="record-logs" if entity.resource not in {"file-uploads", "google-drive-sync"} else "portal-logs",
            payload={
                "summary": summary,
                "action": action,
                "entityTitle": title,
                "entityType": entity.resource,
                "occurredAt": iso_utc(utcnow()),
                "correlationId": str(entity.id),
            },
            status="active",
            created_by=user.id,
            updated_by=user.id,
            record_time=utcnow(),
        ))


async def assert_writable(db: AsyncSession, resource: str) -> None:
    if resource in READ_ONLY:
        raise HTTPException(405, "This resource is read-only")
    row = await db.get(AppSetting, "app-config")
    if row and (row.value or {}).get("system", {}).get("readOnlyMode"):
        raise HTTPException(403, "System is in read-only mode")


def parse_limit(raw: str | None) -> int:
    if raw in {"all", "-1"}:
        return 100
    try:
        return min(100, max(1, int(raw or 20)))
    except ValueError:
        return 20


def apply_status_filter(filters: list, status: str | None) -> None:
    if not status or status in {"all", "all-status"}:
        filters.append(Entity.status.notin_(("archived", "deleted")))
        return
    values = [part for part in status.split(",") if part]
    if values:
        filters.append(Entity.status.in_(values))


async def apply_side_effects(db: AsyncSession, row: Entity, source_payload: dict | None = None) -> None:
    if row.resource == "users":
        await sync_login_user(db, row, source_payload or row.payload or {})
    if row.resource == "roles":
        await refresh_role_users(db, row)
    await sync_domain_row(db, row)


def router_for(path: str, resource: str) -> APIRouter:
    router = APIRouter(prefix=f"/{path}", tags=[path.split("/")[0]], dependencies=[Depends(authorize_resource(resource))])

    @router.get("")
    async def list_items(request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        q = request.query_params.get("q") or request.query_params.get("search")
        page = max(1, int(request.query_params.get("page") or 1))
        limit = parse_limit(request.query_params.get("limit"))
        filters = [Entity.resource == resource]
        if await creator_only(db, user, resource):
            filters.append(Entity.created_by == user.id)
        apply_status_filter(filters, request.query_params.get("status"))
        stage = request.query_params.get("stage")
        if stage and stage not in {"all"}:
            stages = [part for part in stage.split(",") if part]
            if "__empty__" in stages:
                filters.append(Entity.stage.is_(None))
            elif stages:
                filters.append(Entity.stage.in_(stages))
        if q:
            filters.append(func.cast(Entity.payload, String).ilike(f"%{q}%"))
        start = parse_instant(request.query_params.get("startDate"))
        end = parse_instant(request.query_params.get("endDate"), end_of_day=True)
        if start:
            filters.append(Entity.record_time >= start)
        if end:
            filters.append(Entity.record_time <= end)
        for key, value in request.query_params.items():
            if key in QUERY_KEYS or value in {"", "all"}:
                continue
            filters.append(Entity.payload[key].as_string() == value)
        total = await db.scalar(select(func.count()).select_from(Entity).where(*filters)) or 0
        sort = request.query_params.get("sort") or "-updatedAt"
        desc = sort.startswith("-")
        key = sort.lstrip("-")
        column = {
            "createdAt": Entity.created_at,
            "updatedAt": Entity.updated_at,
            "recordTime": Entity.record_time,
            "meetingDate": Entity.record_time,
        }.get(key, Entity.updated_at)
        stmt = select(Entity).where(*filters).order_by(column.desc() if desc else column.asc(), Entity.id)
        rows = (await db.scalars(stmt.offset((page - 1) * limit).limit(limit))).all()
        return {"data": [stamp(row) for row in rows], "meta": {"page": page, "limit": limit, "total": total, "totalPages": max(1, math.ceil(total / limit))}}

    @router.get("/options")
    async def options(request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        limit = min(200, int(request.query_params.get("limit") or 100))
        q = (request.query_params.get("q") or "").lower()
        option_filters = [Entity.resource == resource, Entity.status == "active"]
        if await creator_only(db, user, resource): option_filters.append(Entity.created_by == user.id)
        rows = (await db.scalars(select(Entity).where(*option_filters).order_by(Entity.updated_at.desc()).limit(500))).all()
        value_field = request.query_params.get("valueField") or "id"
        exclude_id = request.query_params.get("excludeId")
        items = []
        for row in rows:
            payload = stamp(row)
            label = str(payload.get("name") or payload.get("title") or payload.get("code") or row.id)
            if q and q not in label.lower():
                continue
            items.append({"id": str(row.id), "label": label, "value": str(payload.get(value_field, row.id)), "parentId": payload.get("parentId"), "meta": {"id": str(row.id), "name": payload.get("name") or label, "code": payload.get("code")}})
        if exclude_id:
            blocked = {exclude_id}
            changed = True
            while changed:
                changed = False
                for item in items:
                    if item["parentId"] in blocked and item["id"] not in blocked:
                        blocked.add(item["id"])
                        changed = True
            items = [item for item in items if item["id"] not in blocked]
        if request.query_params.get("hierarchy") == "true":
            by_parent: dict[str, list] = {}
            for item in items:
                by_parent.setdefault(str(item.get("parentId") or ""), []).append(item)
            ordered: list[dict] = []
            def walk(parent: str, depth: int) -> None:
                for item in sorted(by_parent.get(parent, []), key=lambda row: row["label"]):
                    ordered.append({**item, "label": f"{'- ' * depth}{item['meta']['name']}", "meta": {**item["meta"], "depth": depth, "parentId": item.get("parentId")}})
                    walk(item["id"], depth + 1)
            walk("", 0)
            items = ordered
        return {"data": items[:limit]}

    @router.get("/counts")
    async def counts(request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        group = request.query_params.get("groupBy") or "stage"
        count_filters = [Entity.resource == resource, Entity.status.notin_(("archived", "deleted"))]
        if await creator_only(db, user, resource): count_filters.append(Entity.created_by == user.id)
        rows = (await db.scalars(select(Entity).where(*count_filters))).all()
        groups: dict[str, int] = {}
        unassigned = 0
        for row in rows:
            item = stamp(row)
            value = item.get(group)
            if value in {None, ""}:
                unassigned += 1
            else:
                groups[str(value)] = groups.get(str(value), 0) + 1
        return {"data": {"total": len(rows), "unassigned": unassigned, "groups": groups}}

    @router.post("")
    async def create(request: Request, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await assert_writable(db, resource)
        row_id = uuid.uuid4()
        content_type = request.headers.get("content-type") or ""
        if content_type.startswith("multipart/form-data"):
            form = await request.form()
            upload = next((value for value in form.values() if isinstance(value, StarletteUploadFile)), None)
            payload = {key: str(value) for key, value in form.items() if not isinstance(value, StarletteUploadFile)}
            if upload:
                content = await upload.read()
                filename = safe_name(upload.filename or "file")
                extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
                if extension not in settings.allowed_upload_extensions:
                    raise HTTPException(415, "File extension is not allowed")
                if len(content) > settings.max_upload_size_mb * 1024 * 1024:
                    raise HTTPException(413, "File exceeds the configured upload limit")
                detected = detect_upload_type(content, extension)
                object_key = f"{resource}/{row_id}/{filename}"
                await put_bytes(object_key, content, detected)
                payload.update({"fileName": filename, "name": filename, "mimeType": detected, "sizeBytes": len(content), "objectKey": object_key, "url": f"/api/v2/files/{row_id}", "status": "ready"})
        else:
            payload = await request.json()
        raw_payload = dict(payload)
        payload = await normalize_identity_payload(db, resource, payload, row_id)
        payload = strip_secrets(dict(payload))
        await validate_record_payload(db, resource, payload)
        await validate_department_parent(db, resource, row_id, payload)
        status = payload.pop("status", "active")
        stage = payload.pop("stage", None)
        row = Entity(id=row_id, resource=resource, payload=payload, status=status, stage=stage, created_by=user.id, updated_by=user.id, record_time=extract_record_time(payload) or utcnow())
        db.add(row)
        await db.flush()
        await apply_side_effects(db, row, raw_payload)
        await audit(db, row, user, "created", f"{user.name} created this record")
        await db.commit()
        await db.refresh(row)
        return {"data": stamp(row)}

    @router.post("/bulk-delete")
    async def bulk_delete(body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await assert_writable(db, resource)
        ids = []
        for raw in body.get("ids", [])[:500]:
            row = await entity_or_404(db, resource, raw)
            row.status = "deleted"
            row.deleted_at = utcnow()
            row.version += 1
            await apply_side_effects(db, row)
            ids.append(raw)
            await audit(db, row, user, "deleted", f"{user.name} deleted this record")
        await db.commit()
        return {"data": {"ids": ids}}

    @router.get("/{entity_id}")
    async def get_item(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        return {"data": stamp(await entity_or_404(db, resource, entity_id))}

    @router.patch("/{entity_id}")
    @router.put("/{entity_id}")
    async def update(entity_id: str, body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await assert_writable(db, resource)
        row = await entity_or_404(db, resource, entity_id)
        expected = body.pop("version", None)
        if expected is not None and expected != row.version:
            raise HTTPException(409, "Record was changed by another user")
        raw_body = dict(body)
        merged = await normalize_identity_payload(db, resource, {**(row.payload or {}), **body}, row.id)
        await validate_record_payload(db, resource, merged)
        await validate_department_parent(db, resource, entity_id, merged)
        if "status" in raw_body:
            row.status = str(raw_body["status"])
        if "stage" in raw_body:
            row.stage = raw_body["stage"]
        merged.pop("status", None)
        merged.pop("stage", None)
        row.payload = strip_secrets(merged)
        row.updated_by = user.id
        row.updated_at = utcnow()
        row.record_time = extract_record_time(row.payload) or row.record_time
        row.version += 1
        await apply_side_effects(db, row, {**merged, **raw_body})
        await audit(db, row, user, "updated", f"{user.name} updated this record")
        await db.commit()
        await db.refresh(row)
        return {"data": stamp(row)}

    @router.delete("/{entity_id}")
    async def soft_delete(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await assert_writable(db, resource)
        row = await entity_or_404(db, resource, entity_id)
        row.status = "deleted"
        row.deleted_at = utcnow()
        row.version += 1
        await apply_side_effects(db, row)
        await audit(db, row, user, "deleted", f"{user.name} deleted this record")
        await db.commit()
        return {"data": {"id": entity_id}}

    @router.delete("/{entity_id}/purge")
    async def purge(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await assert_writable(db, resource)
        row = await entity_or_404(db, resource, entity_id)
        if resource == "users" and row.id == user.id:
            raise HTTPException(409, "You cannot purge your own account")
        if resource == "roles":
            assigned = await db.scalar(select(func.count()).select_from(User).where(User.role_id == row.id))
            if assigned:
                raise HTTPException(409, f"Role is assigned to {assigned} users")
        if (row.payload or {}).get("objectKey"):
            await delete_object(row.payload["objectKey"])
        if resource == "users":
            account = await db.get(User, row.id)
            if account:
                await db.delete(account)
                await db.flush()
        await db.delete(row)
        await db.commit()
        return {"data": {"id": entity_id}}

    async def lifecycle(entity_id: str, status: str, db: AsyncSession, user: User):
        await assert_writable(db, resource)
        row = await entity_or_404(db, resource, entity_id)
        row.status = status
        row.version += 1
        row.updated_at = utcnow()
        if status == "archived":
            row.archived_at = utcnow()
        elif status == "active":
            row.archived_at = None
            row.deleted_at = None
        await apply_side_effects(db, row)
        await audit(db, row, user, status, f"{user.name} {status} this record")
        await db.commit()
        await db.refresh(row)
        return {"data": stamp(row)}

    @router.post("/{entity_id}/archive")
    async def archive(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        return await lifecycle(entity_id, "archived", db, user)

    @router.post("/{entity_id}/restore")
    async def restore(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        return await lifecycle(entity_id, "active", db, user)

    @router.patch("/{entity_id}/stage")
    async def stage(entity_id: str, body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await assert_writable(db, resource)
        row = await entity_or_404(db, resource, entity_id)
        row.stage = body.get("stage")
        row.version += 1
        await audit(db, row, user, "transitioned", f"{user.name} changed the stage")
        await db.commit()
        await db.refresh(row)
        return {"data": stamp(row)}

    @router.get("/{entity_id}/neighbors")
    async def neighbors(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        ids = list((await db.scalars(select(Entity.id).where(Entity.resource == resource, Entity.status != "deleted").order_by(Entity.updated_at.desc()))).all())
        uid = uuid.UUID(entity_id)
        if uid not in ids:
            raise HTTPException(404, "Not found")
        index = ids.index(uid)
        return {"data": {"previousId": str(ids[index - 1]) if index else None, "nextId": str(ids[index + 1]) if index + 1 < len(ids) else None}}

    @router.get("/{entity_id}/favorite")
    async def get_favorite(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await entity_or_404(db, resource, entity_id)
        row = await db.scalar(select(Favorite).where(Favorite.user_id == user.id, Favorite.entity_id == uuid.UUID(entity_id)))
        return {"data": {"isFavorite": bool(row)}}

    @router.put("/{entity_id}/favorite")
    async def set_favorite(entity_id: str, body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await entity_or_404(db, resource, entity_id)
        uid = uuid.UUID(entity_id)
        existing = await db.scalar(select(Favorite).where(Favorite.user_id == user.id, Favorite.entity_id == uid))
        desired = bool(body.get("isFavorite"))
        if desired and not existing:
            db.add(Favorite(user_id=user.id, entity_id=uid))
        if not desired and existing:
            await db.delete(existing)
        await db.commit()
        return {"data": {"isFavorite": desired}}

    @router.get("/{entity_id}/comments")
    async def comments(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await entity_or_404(db, resource, entity_id)
        rows = (await db.scalars(select(Comment).where(Comment.entity_id == uuid.UUID(entity_id)).order_by(Comment.created_at.desc()))).all()
        authors = (await db.scalars(select(User).where(User.id.in_({row.author_id for row in rows if row.author_id} or {user.id})))).all()
        by_id = {row.id: row for row in authors}
        data = [{
            "id": str(row.id),
            "entityType": resource,
            "entityId": entity_id,
            "body": row.body,
            "author": person(by_id.get(row.author_id) or user),
            "createdAt": iso_utc(row.created_at),
            "editedAt": iso_utc(row.edited_at),
        } for row in rows]
        return {"data": data, "meta": {"page": 1, "limit": len(data) or 20, "total": len(data)}}

    @router.post("/{entity_id}/comments")
    async def add_comment(entity_id: str, body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        row = await entity_or_404(db, resource, entity_id)
        comment = Comment(entity_id=row.id, body=str(body.get("body") or ""), author_id=user.id)
        db.add(comment)
        await audit(db, row, user, "comment.added", f"{user.name} added a comment")
        await db.commit()
        await db.refresh(comment)
        return {"data": {"id": str(comment.id), "entityType": resource, "entityId": entity_id, "body": comment.body, "author": person(user), "createdAt": iso_utc(comment.created_at)}}

    @router.patch("/{entity_id}/comments/{comment_id}")
    async def edit_comment(entity_id: str, comment_id: str, body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        row = await db.scalar(select(Comment).where(Comment.id == uuid.UUID(comment_id), Comment.entity_id == uuid.UUID(entity_id)))
        if not row:
            raise HTTPException(404, "Comment not found")
        row.body = str(body.get("body") or "")
        row.edited_at = utcnow()
        await db.commit()
        return {"data": {"id": comment_id, "entityId": entity_id, "entityType": resource, "body": row.body, "author": person(user), "createdAt": iso_utc(row.created_at), "editedAt": iso_utc(row.edited_at)}}

    @router.delete("/{entity_id}/comments/{comment_id}")
    async def delete_comment(entity_id: str, comment_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        await db.execute(delete(Comment).where(Comment.id == uuid.UUID(comment_id), Comment.entity_id == uuid.UUID(entity_id)))
        await db.commit()
        return {"data": {"id": comment_id}}

    @router.get("/{entity_id}/activity")
    async def activity(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        rows = (await db.scalars(select(Activity).where(Activity.entity_id == uuid.UUID(entity_id)).order_by(Activity.occurred_at.desc()))).all()
        return {"data": [{
            "id": str(row.id),
            "entityType": resource,
            "entityId": entity_id,
            "action": row.action,
            "summary": row.summary,
            "actor": person(user),
            "occurredAt": iso_utc(row.occurred_at),
            "metadata": row.metadata_,
        } for row in rows], "meta": {"page": 1, "limit": len(rows) or 20, "total": len(rows)}}

    @router.get("/{entity_id}/attachments")
    async def attachments(entity_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        row = await entity_or_404(db, resource, entity_id)
        return {"data": (row.payload or {}).get("attachments", [])}

    @router.put("/{entity_id}/attachments")
    @router.post("/{entity_id}/attachments")
    async def replace_attachments(entity_id: str, body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(current_user)):
        row = await entity_or_404(db, resource, entity_id)
        files = body.get("files") or body.get("attachments") or []
        row.payload = {**(row.payload or {}), "attachments": files}
        await audit(db, row, user, "attachments.updated", f"{user.name} updated attachments")
        await db.commit()
        return {"data": files}

    return router
