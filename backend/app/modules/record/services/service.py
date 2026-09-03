"""Typed-table collection service — replaces Entity JSONB CRUD for frontend adapters."""

from __future__ import annotations

import math
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy import String, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.modules.record.services.creator_scope import creator_only
from app.core.concurrency import VERSIONED_KINDS, require_matching_version
from app.core.datetime import extract_record_time, utcnow
from typing import Any as User
from app.modules.record.model import Entity, Record, RecordAttribute, RecordType
from app.modules.people_access.service import normalize_identity_payload, people, strip_secrets
from app.modules.record.domain.map import RECORD_RESOURCES
from app.modules.record.services.kind import CollectionSpec
from app.modules.record.services.record_collections import RecordApplicationService
from app.modules.record.services.support_collections import SupportApplicationService
from app.modules.record.services.stamp import assert_writable, entity_or_404, stamp, apply_side_effects, audit
from app.integrations.objectstore import delete_object, put_bytes, safe_name
from app.shared.upload_validation import detect_upload_type
from app.shared.pagination import parse_limit
from app.modules.admin_config.service import runtime


class CollectionService:
    """Facade that dispatches to typed application services by collection kind."""

    def __init__(
        self,
        resource: str | None = None,
        *,
        type_code: str | None = None,
    ):
        spec = CollectionSpec(resource, type_code=type_code)
        self._spec = spec
        self.resource = spec.resource
        self.type_code = spec.type_code
        self.records = RecordApplicationService(self)
        self.support = SupportApplicationService(self)

    def kind(self) -> str:
        return self._spec.kind()

    def resolve_type_code(self) -> str:
        if self.type_code:
            return self.type_code
        code = RECORD_RESOURCES.get(self.resource or "")
        if not code:
            from fastapi import HTTPException
            raise HTTPException(404, "Record type not found")
        return code

    async def get_record_row_or_404(self, db: AsyncSession, entity_id: str, user: User | None = None) -> Record:
        try:
            uid = uuid.UUID(str(entity_id))
        except ValueError as exc:
            raise HTTPException(404, "Not found") from exc
        row = await db.get(Record, uid)
        if not row:
            raise HTTPException(404, "Not found")
        expected_code = self.resolve_type_code()
        type_row = await db.get(RecordType, row.record_type_id) if row.record_type_id else None
        actual_code = type_row.code if type_row else row.record_type_code
        if actual_code != expected_code:
            raise HTTPException(404, "Not found")
        if user is None:
            return row
        import app.modules.record.services.type_access as type_access
        from app.core.privileged import is_unrestricted

        if not is_unrestricted(user):
            if type_row:
                await type_access.require_type_access(db, type_row, user)
            if not await type_access.record_visible_to_user(db, row, user):
                raise HTTPException(404, "Not found")
        return row

    async def actor_officer_id(self, db: AsyncSession, user: User) -> uuid.UUID | None:
        officer = await people.ensure_officer_for_user(db, user)
        return officer.id

    def _assert_version(self, current: Any, expected: Any) -> None:
        if self.kind() in VERSIONED_KINDS:
            require_matching_version(current, expected)

    async def list_items(self, db: AsyncSession, user: User, params: dict) -> dict:
        kind = self.kind()
        page = max(1, int(params.get("page") or 1))
        config = await runtime.load_app_config(db)
        default_limit = runtime.general_defaults(config)["defaultPageSize"]
        limit = parse_limit(params.get("limit"), default=default_limit)
        q = params.get("q") or params.get("search")
        status = params.get("status")

        if kind == "record":
            return await self.records.list_items(db, user, params, page, limit, q, status)
        return await self.support.list_items(db, user, params, page, limit, q, status)

    async def get_item(self, db: AsyncSession, entity_id: str, user: User | None = None) -> dict:
        kind = self.kind()
        try:
            uuid.UUID(entity_id)
        except ValueError as exc:
            raise HTTPException(404, "Not found") from exc
        if kind == "record":
            if user is None:
                raise HTTPException(401, "Authentication required")
            return await self.records.get_item(db, user, entity_id)
        return await self.support.get_item(db, entity_id, user)

    async def create(self, db: AsyncSession, user: User, payload: dict, raw_payload: dict | None = None) -> dict:
        await assert_writable(db, self.resource)
        kind = self.kind()
        if kind == "record":
            return await self.records.create(db, user, payload)
        return await self.support.create(db, user, payload, raw_payload)

    async def update(self, db: AsyncSession, user: User, entity_id: str, body: dict) -> dict:
        await assert_writable(db, self.resource)
        kind = self.kind()
        current = await self.get_item(db, entity_id, user)
        expected = body.pop("version", None)
        self._assert_version(current.get("version"), expected)

        if kind == "record":
            return await self.records.update(db, user, entity_id, body, current)
        return await self.support.update(db, user, entity_id, body)

    async def duplicate(self, db: AsyncSession, user: User, entity_id: str) -> dict:
        if self.kind() != "record":
            return await self.support.duplicate(db, user, entity_id)
        raise HTTPException(404, "Not found")

    async def set_active(self, db: AsyncSession, user: User, entity_id: str, active: bool) -> dict:
        if self.kind() != "record":
            return await self.support.set_active(db, user, entity_id, active)
        raise HTTPException(404, "Not found")

    async def attach_file(self, db: AsyncSession, user: User, entity_id: str, file_payload: dict, expected=None) -> dict:
        if self.kind() != "record":
            raise HTTPException(404, "Not found")
        return await self.records.attach_file(db, user, entity_id, file_payload, expected)

    async def detach_file(self, db: AsyncSession, user: User, entity_id: str, file_id: str, expected=None) -> dict:
        if self.kind() != "record":
            raise HTTPException(404, "Not found")
        return await self.records.detach_file(db, user, entity_id, file_id, expected)

    async def _get_model(self, db, kind, entity_id):
        uid = uuid.UUID(entity_id)
        mapping = {
            "record_type": RecordType,
            "record_attribute": RecordAttribute,
        }
        row = await db.get(mapping[kind], uid)
        if not row:
            raise HTTPException(404, "Not found")
        return row

    async def soft_delete(self, db: AsyncSession, user: User, entity_id: str, body: dict | None = None) -> dict:
        await assert_writable(db, self.resource)
        kind = self.kind()
        expected = (body or {}).get("version")
        if kind == "record":
            return await self.records.soft_delete(db, user, entity_id, expected)
        return await self.support.soft_delete(db, user, entity_id, expected)

    async def purge(self, db: AsyncSession, user: User, entity_id: str, body: dict | None = None) -> dict:
        await assert_writable(db, self.resource)
        kind = self.kind()
        expected = (body or {}).get("version")
        if kind == "record":
            return await self.records.purge(db, user, entity_id, expected)
        return await self.support.purge(db, user, entity_id, expected)

    async def lifecycle(self, db: AsyncSession, user: User, entity_id: str, status: str, body: dict | None = None) -> dict:
        await assert_writable(db, self.resource)
        expected = (body or {}).get("version")
        if self.kind() == "record":
            return await self.records.lifecycle(db, user, entity_id, status, expected)
        if self.kind() == "entity":
            return await self.support.lifecycle(db, user, entity_id, status, expected)
        payload = {"status": status}
        if expected is not None:
            payload["version"] = expected
        return await self.update(db, user, entity_id, payload)

    async def set_stage(self, db: AsyncSession, user: User, entity_id: str, stage: Any, body: dict | None = None) -> dict:
        await assert_writable(db, self.resource)
        kind = self.kind()
        expected = (body or {}).get("version")
        if kind == "entity":
            return await self.support.set_stage(db, user, entity_id, stage, expected)
        if kind != "record":
            raise HTTPException(404, "Not found")
        return await self.records.set_stage(db, user, entity_id, stage, expected)

    async def create_upload(self, db: AsyncSession, user: User, request) -> dict:
        await assert_writable(db, self.resource)
        officer_id = await self.actor_officer_id(db, user)
        row_id = uuid.uuid4()
        form = await request.form()
        upload = next((value for value in form.values() if isinstance(value, StarletteUploadFile)), None)
        payload = {key: str(value) for key, value in form.items() if not isinstance(value, StarletteUploadFile)}
        pending_object: tuple[str, bytes, str] | None = None
        if upload:
            content = await upload.read()
            filename = safe_name(upload.filename or "file")
            extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            policy = runtime.upload_policy(await runtime.load_app_config(db))
            if extension not in policy["allowedUploadExtensions"]:
                raise HTTPException(415, "File extension is not allowed")
            if len(content) > policy["maxUploadSizeMb"] * 1024 * 1024:
                raise HTTPException(413, "File exceeds the configured upload limit")
            detected = detect_upload_type(content, extension)
            object_key = f"{self.resource}/{row_id}/{filename}"
            pending_object = (object_key, content, detected)
            payload.update({
                "fileName": filename,
                "name": filename,
                "mimeType": detected,
                "sizeBytes": len(content),
                "objectKey": object_key,
                "url": f"/api/v2/files/{row_id}",
            })
            if self.kind() == "entity":
                payload["status"] = "pending"

        async def store_object() -> None:
            if pending_object is None:
                return
            object_key, content, detected = pending_object
            await put_bytes(object_key, content, detected, db)

        if self.kind() == "entity":
            payload = {**payload, "id": str(row_id)}
            created = await self._create_entity(db, user, payload, payload, row_id=row_id)
            try:
                await store_object()
            except Exception:
                try:
                    failed = await entity_or_404(db, self.resource, str(row_id))
                    failed.status = "failed"
                    await db.flush()
                except Exception:
                    pass
                raise
            if pending_object:
                return await self.update(db, user, str(row_id), {"status": "active", "version": created.get("version")})
            return created
        created = await self.create(db, user, payload, payload)
        try:
            await store_object()
        except Exception:
            try:
                await self.soft_delete(db, user, str(created["id"]), {"version": created.get("version")})
            except Exception:
                pass
            raise
        return created

    async def _list_entity(self, db, user, params, page, limit, q, status):
        filters = [Entity.resource == self.resource]
        if await creator_only(db, user, self.resource):
            filters.append(Entity.created_by == user.id)
        if not status or status in {"all", "all-status"}:
            filters.append(Entity.status.notin_(("archived", "deleted")))
        else:
            values = [part for part in status.split(",") if part]
            if values:
                filters.append(Entity.status.in_(values))
        if q:
            filters.append(func.cast(Entity.payload, String).ilike(f"%{q}%"))
        total = await db.scalar(select(func.count()).select_from(Entity).where(*filters)) or 0
        sort = params.get("sort") or "-updatedAt"
        desc = sort.startswith("-")
        key = sort.lstrip("-")
        column = {"createdAt": Entity.created_at, "updatedAt": Entity.updated_at, "recordTime": Entity.record_time}.get(key, Entity.updated_at)
        rows = (await db.scalars(select(Entity).where(*filters).order_by(column.desc() if desc else column.asc(), Entity.id).offset((page - 1) * limit).limit(limit))).all()
        return {"data": [stamp(row) for row in rows], "meta": {"page": page, "limit": limit, "total": total, "totalPages": max(1, math.ceil(total / limit))}}

    async def _create_entity(self, db, user, payload, raw_payload, row_id=None):
        row_id = row_id or uuid.uuid4()
        payload = await normalize_identity_payload(db, self.resource, payload, row_id, actor=user)
        payload = strip_secrets(dict(payload))
        status = payload.pop("status", "active")
        stage = payload.pop("stage", None)
        row = Entity(id=row_id, resource=self.resource, payload=payload, status=status, stage=stage, created_by=user.id, updated_by=user.id, record_time=extract_record_time(payload) or utcnow())
        db.add(row)
        await db.flush()
        await apply_side_effects(db, row, raw_payload)
        await audit(db, row, user, "created", f"{user.name} created this record")
        await db.flush()
        await db.refresh(row)
        return stamp(row)

    async def _update_entity(self, db, user, entity_id, body):
        row = await entity_or_404(db, self.resource, entity_id)
        expected = body.pop("version", None)
        self._assert_version(row.version, expected)
        raw_body = dict(body)
        merged = await normalize_identity_payload(db, self.resource, {**(row.payload or {}), **body}, row.id, actor=user)
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
        await db.flush()
        await db.refresh(row)
        return stamp(row)

    async def _soft_delete_entity(self, db, user, entity_id, expected=None):
        row = await entity_or_404(db, self.resource, entity_id)
        self._assert_version(row.version, expected)
        row.status = "deleted"
        row.deleted_at = utcnow()
        row.version += 1
        await apply_side_effects(db, row)
        await audit(db, row, user, "deleted", f"{user.name} deleted this record")
        await db.flush()
        return {"id": entity_id}

    async def _purge_entity(self, db, user, entity_id, expected=None):
        row = await entity_or_404(db, self.resource, entity_id)
        self._assert_version(row.version, expected)
        object_key = (row.payload or {}).get("objectKey")
        row.status = "pending_purge"
        await db.flush()
        if object_key:
            await delete_object(object_key)
        row = await entity_or_404(db, self.resource, entity_id)
        await db.delete(row)
        await db.flush()
        return {"id": entity_id}
