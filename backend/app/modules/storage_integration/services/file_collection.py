"""Storage-owned file upload collection service."""

from __future__ import annotations

import math
import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.datetime import iso_utc, utcnow
from app.integrations.objectstore import delete_object, put_bytes, safe_name
from app.modules.admin_config.service import runtime
from app.modules.record.service import actor_officer_id
from app.modules.storage_integration.model import File
from app.modules.storage_integration.repository import StorageRepository
from app.shared.pagination import parse_limit
from app.shared.upload_validation import detect_upload_type


def _payload(row: File) -> dict:
    return {
        "id": str(row.id),
        "name": row.nam,
        "fileName": row.nam,
        "objectKey": row.path,
        "sizeBytes": row.file_size,
        "mimeType": row.mime_type,
        "url": row.direct_url or f"/api/v2/files/{row.id}",
        "status": row.status,
        "createdAt": iso_utc(row.created_at),
        "updatedAt": iso_utc(row.updated_at),
        "version": 1,
    }


class StorageFileCollectionService:
    resource = "file-uploads"

    async def list_items(self, db, user, params) -> dict:
        page = max(1, int(params.get("page") or 1))
        defaults = runtime.general_defaults(await runtime.load_app_config(db))
        limit = parse_limit(params.get("limit"), default=defaults["defaultPageSize"])
        filters = [File.status != "trash"]
        q = params.get("q") or params.get("search")
        if q:
            filters.append(File.nam.ilike(f"%{q}%"))
        total = await db.scalar(select(func.count()).select_from(File).where(*filters)) or 0
        rows = (await db.scalars(
            select(File).where(*filters).order_by(File.updated_at.desc()).offset((page - 1) * limit).limit(limit)
        )).all()
        return {"data": [_payload(row) for row in rows], "meta": {"page": page, "limit": limit, "total": total, "totalPages": max(1, math.ceil(total / limit))}}

    async def get_item(self, db, entity_id: str, user=None) -> dict:
        try:
            row = await StorageRepository(db).file(uuid.UUID(entity_id))
        except ValueError as exc:
            raise HTTPException(404, "Not found") from exc
        if not row:
            raise HTTPException(404, "Not found")
        return _payload(row)

    async def create(self, db, user, payload: dict, raw_payload=None) -> dict:
        officer_id = await actor_officer_id(db, user)
        row = File(
            nam=str(payload.get("name") or payload.get("fileName") or "file"),
            path=str(payload.get("objectKey") or payload.get("path") or ""),
            file_size=int(payload.get("sizeBytes") or 0),
            mime_type=payload.get("mimeType"),
            storage_type=payload.get("storageType") or "s3",
            direct_url=payload.get("url"),
            source_table="file-uploads",
            status=str(payload.get("status") or "active"),
            created_by=officer_id,
            updated_by=officer_id,
        )
        await StorageRepository(db).add(row)
        await db.refresh(row)
        return _payload(row)

    async def create_upload(self, db, user, request) -> dict:
        row_id = uuid.uuid4()
        form = await request.form()
        upload = next((value for value in form.values() if isinstance(value, StarletteUploadFile)), None)
        if upload is None:
            return await self.create(db, user, {key: str(value) for key, value in form.items()})
        content = await upload.read()
        filename = safe_name(upload.filename or "file")
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        policy = runtime.upload_policy(await runtime.load_app_config(db))
        if extension not in policy["allowedUploadExtensions"]:
            raise HTTPException(415, "File extension is not allowed")
        if len(content) > policy["maxUploadSizeMb"] * 1024 * 1024:
            raise HTTPException(413, "File exceeds the configured upload limit")
        mime_type = detect_upload_type(content, extension)
        object_key = f"{self.resource}/{row_id}/{filename}"
        officer_id = await actor_officer_id(db, user)
        row = File(
            id=row_id,
            nam=filename,
            path=object_key,
            file_size=len(content),
            mime_type=mime_type,
            storage_type="s3",
            direct_url=f"/api/v2/files/{row_id}",
            source_table="file-uploads",
            status="pending",
            created_by=officer_id,
            updated_by=officer_id,
        )
        await StorageRepository(db).add(row)
        try:
            await put_bytes(object_key, content, mime_type, db)
        except Exception:
            row.status = "failed"
            await db.flush()
            raise
        row.status = "active"
        await db.flush()
        return _payload(row)

    async def update(self, db, user, entity_id: str, body: dict) -> dict:
        row = await StorageRepository(db).file(uuid.UUID(entity_id))
        if not row:
            raise HTTPException(404, "Not found")
        if "name" in body or "fileName" in body:
            row.nam = str(body.get("name") or body.get("fileName"))
        if "objectKey" in body or "path" in body:
            row.path = str(body.get("objectKey") or body.get("path"))
        if "status" in body:
            row.status = str(body["status"])
        row.updated_by = await actor_officer_id(db, user)
        row.updated_at = utcnow()
        await db.flush()
        return _payload(row)

    async def soft_delete(self, db, user, entity_id: str, body=None) -> dict:
        row = await StorageRepository(db).file(uuid.UUID(entity_id))
        if not row:
            raise HTTPException(404, "Not found")
        row.status = "trash"
        await db.flush()
        return {"id": entity_id}

    async def purge(self, db, user, entity_id: str, body=None) -> dict:
        row = await StorageRepository(db).file(uuid.UUID(entity_id))
        if not row:
            raise HTTPException(404, "Not found")
        row.status = "pending_purge"
        await db.flush()
        if row.path:
            await delete_object(row.path, db)
        await StorageRepository(db).delete(row)
        return {"id": entity_id}

    async def lifecycle(self, db, user, entity_id: str, status: str, body=None) -> dict:
        return await self.update(db, user, entity_id, {"status": status})

    async def set_stage(self, db, user, entity_id, stage, body=None):
        raise HTTPException(404, "Not found")


__all__ = ["StorageFileCollectionService"]
