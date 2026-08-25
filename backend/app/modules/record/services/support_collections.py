"""Typed support collections — record types/attributes, files, audit logs, Entity bags."""

from __future__ import annotations

import math
import uuid

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import iso_utc, utcnow
from app.core.errors import DomainError
from app.models.audit import AuditLog
from app.models.people import User
from app.models.record import RecordAttribute, RecordType
from app.models.storage import File
from app.modules.admin_config.services.configuration import serialize_record_type
from app.modules.people_access.services.identity import strip_secrets
from app.modules.record.services.stamp import apply_side_effects, audit, entity_or_404, stamp
from app.modules.storage_integration.services.storage import delete_object


class SupportApplicationService:
    def __init__(self, host):
        self.host = host

    def kind(self) -> str:
        return self.host.kind()

    async def list_items(self, db: AsyncSession, user: User, params: dict, page: int, limit: int, q, status) -> dict:
        kind = self.kind()
        if kind == "record_type":
            from app.core.privileged import is_unrestricted
            import app.modules.record.services.type_access as type_access

            stmt = select(RecordType)
            if not is_unrestricted(user):
                type_ids = await type_access.permitted_type_ids(db, await type_access.actor_organization_id(db, user))
                if not type_ids:
                    return {"data": [], "meta": {"page": page, "limit": limit, "total": 0, "totalPages": 1}}
                stmt = stmt.where(RecordType.id.in_(type_ids))
            total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
            rows = (await db.scalars(
                stmt.order_by(RecordType.updated_at.desc()).offset((page - 1) * limit).limit(limit)
            )).all()
            access = await type_access.permission_payload(db, [row.id for row in rows])
            data = [{**serialize_record_type(row), **access.get(row.id, {})} for row in rows]
            return {"data": data, "meta": {"page": page, "limit": limit, "total": total, "totalPages": max(1, math.ceil(total / limit))}}

        if kind == "record_attribute":
            rows = (await db.scalars(select(RecordAttribute).order_by(RecordAttribute.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
            data = [{
                "id": str(row.id), "code": row.code, "name": row.nam or row.code, "dataType": row.data_type,
                **(row.payload or {}), "createdAt": iso_utc(row.created_at), "updatedAt": iso_utc(row.updated_at), "version": 1,
            } for row in rows]
            return {"data": data, "meta": {"page": page, "limit": limit, "total": len(data), "totalPages": 1}}

        if kind == "file":
            rows = (await db.scalars(select(File).where(File.status != "trash").order_by(File.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
            data = [{
                "id": str(row.id), "name": row.nam, "fileName": row.nam, "objectKey": row.path, "sizeBytes": row.file_size,
                "mimeType": row.mime_type, "url": row.direct_url or f"/api/v2/files/{row.id}", "status": row.status,
                "createdAt": iso_utc(row.created_at), "updatedAt": iso_utc(row.updated_at), "version": 1,
            } for row in rows]
            return {"data": data, "meta": {"page": page, "limit": limit, "total": len(data), "totalPages": 1}}

        if kind == "audit":
            source = {"portal-logs": "portal", "system-logs": "system"}.get(self.host.resource, "record")
            filters = [AuditLog.source_log == source] if source != "record" else [AuditLog.source_log.in_(("record", "api", "unknown"))]
            if self.host.resource == "record-logs":
                from app.modules.record.domain.map import TYPE_CODE_TO_RESOURCE, TYPE_UI_DEFAULTS
                doc_codes = [code for code, meta in TYPE_UI_DEFAULTS.items() if meta.get("uiSurface") == "document"]
                doc_resources = [TYPE_CODE_TO_RESOURCE[c] for c in doc_codes if c in TYPE_CODE_TO_RESOURCE]
                allowed = set(doc_codes) | set(doc_resources) | {r.replace("-", "_") for r in doc_resources}
                filters.append(
                    or_(
                        AuditLog.table_name.is_(None),
                        AuditLog.table_name == "",
                        AuditLog.table_name.in_(list(allowed)),
                    )
                )
            total = await db.scalar(select(func.count()).select_from(AuditLog).where(*filters)) or 0
            rows = (await db.scalars(select(AuditLog).where(*filters).order_by(AuditLog.created_at.desc()).offset((page - 1) * limit).limit(limit))).all()
            data = [{
                "id": str(row.id), "summary": row.message or row.action_code, "action": row.action_code,
                "entityType": row.table_name, "occurredAt": iso_utc(row.created_at), "status": row.status_code,
                "detail": row.detail_data,
            } for row in rows]
            return {"data": data, "meta": {"page": page, "limit": limit, "total": total, "totalPages": max(1, math.ceil(total / limit))}}

        if kind == "entity":
            return await self.host._list_entity(db, user, params, page, limit, q, status)

        raise DomainError("UNSUPPORTED", f"Resource {self.host.resource} is not mapped", 501)

    async def get_item(self, db: AsyncSession, entity_id: str, user: User | None = None) -> dict:
        kind = self.kind()
        uid = uuid.UUID(entity_id)
        if kind == "record_type":
            import app.modules.record.services.type_access as type_access

            row = await db.get(RecordType, uid)
            if not row:
                raise HTTPException(404, "Not found")
            await type_access.require_type_access(db, row, user)
            access = await type_access.permission_payload(db, [row.id])
            return {**serialize_record_type(row), **access.get(row.id, {})}
        if kind == "record_attribute":
            row = await db.get(RecordAttribute, uid)
            if not row:
                raise HTTPException(404, "Not found")
            return {
                "id": str(row.id), "code": row.code, "name": row.nam or row.code, "dataType": row.data_type,
                **(row.payload or {}), "version": 1, "createdAt": iso_utc(row.created_at), "updatedAt": iso_utc(row.updated_at),
            }
        if kind == "file":
            row = await db.get(File, uid)
            if not row:
                raise HTTPException(404, "Not found")
            return {
                "id": str(row.id), "name": row.nam, "objectKey": row.path, "sizeBytes": row.file_size,
                "mimeType": row.mime_type, "url": row.direct_url or f"/api/v2/files/{row.id}",
                "status": row.status, "version": 1,
            }
        if kind == "entity":
            return stamp(await entity_or_404(db, self.host.resource, entity_id))
        raise HTTPException(404, "Not found")

    async def create(self, db: AsyncSession, user: User, payload: dict, raw_payload: dict | None = None) -> dict:
        officer_id = await self.host.actor_officer_id(db, user)
        kind = self.kind()
        if kind == "record_type":
            import app.modules.record.services.type_access as type_access

            row = RecordType(
                code=str(payload.get("code") or "").strip(),
                nam=str(payload.get("name") or payload.get("code") or ""),
                description=payload.get("description"),
                is_active=0 if payload.get("status") == "inactive" else 1,
                payload=strip_secrets({k: v for k, v in payload.items() if k not in {"code", "name", "description", "status"}}),
                created_by=officer_id,
                updated_by=officer_id,
            )
            db.add(row)
            await db.flush()
            org_id = await type_access.actor_organization_id(db, user)
            if org_id:
                await type_access.grant(
                    db,
                    row.id,
                    org_id,
                    permission_kind=type_access.OWNER,
                    actor_officer_id=officer_id,
                )
            await db.commit()
            await db.refresh(row)
            return await self.get_item(db, str(row.id), user)
        if kind == "record_attribute":
            row = RecordAttribute(
                code=str(payload.get("code") or "").strip(),
                nam=str(payload.get("name") or payload.get("code") or ""),
                data_type=str(payload.get("dataType") or payload.get("data_type") or "string"),
                payload=strip_secrets(dict(payload)),
                created_by=officer_id,
                updated_by=officer_id,
            )
            db.add(row)
            await db.commit()
            await db.refresh(row)
            return await self.get_item(db, str(row.id), user)
        if kind == "file":
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
            db.add(row)
            await db.commit()
            await db.refresh(row)
            return await self.get_item(db, str(row.id), user)
        if kind == "entity":
            return await self.host._create_entity(db, user, payload, raw_payload or payload)
        raise DomainError("UNSUPPORTED", f"Create not supported for {self.host.resource}", 501)

    async def update(self, db: AsyncSession, user: User, entity_id: str, body: dict) -> dict:
        officer_id = await self.host.actor_officer_id(db, user)
        kind = self.kind()
        if kind == "entity":
            return await self.host._update_entity(db, user, entity_id, body)
        if kind not in {"record_type", "record_attribute", "file"}:
            raise DomainError("UNSUPPORTED", f"Update not supported for {self.host.resource}", 501)
        row = await self.host._get_model(db, kind, entity_id)
        if kind == "record_type":
            import app.modules.record.services.type_access as type_access

            await type_access.require_owner_access(db, row, user)
        for key, value in body.items():
            if key in {"version", "id"}:
                continue
            if kind == "record_type":
                if key == "name":
                    row.nam = str(value)
                elif key == "code":
                    row.code = str(value)
                elif key == "description":
                    row.description = value
                elif key == "status":
                    row.is_active = 0 if value == "inactive" else 1
                else:
                    row.payload = {**(row.payload or {}), key: value}
            elif kind == "record_attribute":
                if key == "name":
                    row.nam = str(value)
                elif key == "code":
                    row.code = str(value)
                elif key in {"dataType", "data_type"}:
                    row.data_type = str(value)
                else:
                    row.payload = {**(row.payload or {}), key: value}
            elif kind == "file":
                if key in {"name", "fileName"}:
                    row.nam = str(value)
                elif key in {"objectKey", "path"}:
                    row.path = str(value)
                elif key == "status":
                    row.status = str(value)
        row.updated_by = officer_id
        row.updated_at = utcnow()
        await db.commit()
        return await self.get_item(db, entity_id, user)

    async def soft_delete(self, db: AsyncSession, user: User, entity_id: str, expected) -> dict:
        kind = self.kind()
        if kind == "file":
            row = await db.get(File, uuid.UUID(entity_id))
            if not row:
                raise HTTPException(404, "Not found")
            row.status = "trash"
            await db.commit()
            return {"id": entity_id}
        if kind == "entity":
            return await self.host._soft_delete_entity(db, user, entity_id, expected)
        return await self.purge(db, user, entity_id, expected)

    async def purge(self, db: AsyncSession, user: User, entity_id: str, expected) -> dict:
        kind = self.kind()
        uid = uuid.UUID(entity_id)
        if kind == "entity":
            return await self.host._purge_entity(db, user, entity_id, expected)
        model = {"record_type": RecordType, "record_attribute": RecordAttribute, "file": File}.get(kind)
        if not model:
            raise HTTPException(404, "Not found")
        row = await db.get(model, uid)
        if not row:
            raise HTTPException(404, "Not found")
        if kind == "record_type":
            import app.modules.record.services.type_access as type_access

            await type_access.require_owner_access(db, row, user)
        if kind == "file":
            row.status = "pending_purge"
            object_key = row.path
            await db.commit()
            if object_key:
                await delete_object(object_key)
            row = await db.get(File, uid)
            if row:
                await db.delete(row)
                await db.commit()
            return {"id": entity_id}
        await db.delete(row)
        await db.commit()
        return {"id": entity_id}

    async def lifecycle(self, db: AsyncSession, user: User, entity_id: str, status: str, expected) -> dict:
        if self.kind() != "entity":
            payload = {"status": status}
            if expected is not None:
                payload["version"] = expected
            return await self.host.update(db, user, entity_id, payload)
        row = await entity_or_404(db, self.host.resource, entity_id)
        self.host._assert_version(row.version, expected)
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
        return stamp(row)

    async def set_stage(self, db: AsyncSession, user: User, entity_id: str, stage, expected) -> dict:
        if self.kind() != "entity":
            raise HTTPException(404, "Not found")
        row = await entity_or_404(db, self.host.resource, entity_id)
        self.host._assert_version(row.version, expected)
        row.stage = stage
        row.version += 1
        await audit(db, row, user, "transitioned", f"{user.name} changed the stage")
        await db.commit()
        await db.refresh(row)
        return stamp(row)
