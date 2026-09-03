"""Typed support collections — record types/attributes, files, audit logs, Entity bags."""

from __future__ import annotations

import math
import uuid

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import iso_utc, utcnow
from app.core.errors import DomainError
from app.platform.audit.model import AuditLog
from typing import Any as User
from app.modules.record.model import RecordAttribute, RecordType
from app.modules.record.services.configuration import serialize_record_type
from app.modules.people_access.service import officer_names_by_ids, strip_secrets
from app.modules.record.services.stamp import apply_side_effects, audit, entity_or_404, stamp


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
            actor_names = await officer_names_by_ids(db, {row.created_by for row in rows if row.created_by})
            data = [{
                "id": str(row.id), "summary": row.message or row.action_code, "action": row.action_code,
                "entityType": row.table_name, "occurredAt": iso_utc(row.created_at), "status": row.status_code,
                "detail": row.detail_data,
                # Canonical actor/target enrichment (shared by record/portal/system views).
                "actor": {"id": str(row.created_by), "name": actor_names.get(row.created_by)} if row.created_by else None,
                "target": row.table_name,
                "message": row.message,
                "statusCode": row.status_code,
                "sourceLog": row.source_log,
                "ipAddress": row.ip_address,
                "createdAt": iso_utc(row.created_at),
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
            await db.flush()
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
            await db.flush()
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
        if kind not in {"record_type", "record_attribute"}:
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
        row.updated_by = officer_id
        row.updated_at = utcnow()
        await db.flush()
        return await self.get_item(db, entity_id, user)

    async def duplicate(self, db: AsyncSession, user: User, entity_id: str) -> dict:
        """Duplicate a record type/attribute as an inactive draft copy."""
        kind = self.kind()
        if kind not in {"record_type", "record_attribute"}:
            raise HTTPException(404, "Not found")
        row = await self.host._get_model(db, kind, entity_id)
        if kind == "record_type":
            import app.modules.record.services.type_access as type_access

            await type_access.require_owner_access(db, row, user)
        officer_id = await self.host.actor_officer_id(db, user)

        model = RecordType if kind == "record_type" else RecordAttribute
        base = f"{row.code}_copy"
        new_code = base
        suffix = 1
        while (await db.scalar(select(func.count()).select_from(model).where(model.code == new_code)) or 0):
            suffix += 1
            new_code = f"{base}_{suffix}"

        if kind == "record_type":
            copy = RecordType(
                code=new_code,
                nam=f"{row.nam or row.code} (copy)",
                description=row.description,
                is_active=0,
                payload=strip_secrets({k: v for k, v in (row.payload or {}).items() if k != "code"}),
                created_by=officer_id,
                updated_by=officer_id,
            )
        else:
            copy = RecordAttribute(
                code=new_code,
                nam=f"{row.nam or row.code} (copy)",
                data_type=row.data_type,
                payload=strip_secrets({**(row.payload or {}), "status": "inactive"}),
                created_by=officer_id,
                updated_by=officer_id,
            )
        db.add(copy)
        await db.flush()
        if kind == "record_type":
            import app.modules.record.services.type_access as type_access

            org_id = await type_access.actor_organization_id(db, user)
            if org_id:
                await type_access.grant(
                    db,
                    copy.id,
                    org_id,
                    permission_kind=type_access.OWNER,
                    actor_officer_id=officer_id,
                )
            await db.flush()
        await db.refresh(copy)
        return await self.get_item(db, str(copy.id), user)

    async def set_active(self, db: AsyncSession, user: User, entity_id: str, active: bool) -> dict:
        """Activate/deactivate: ``is_active`` for RecordType, payload status for RecordAttribute."""
        kind = self.kind()
        if kind not in {"record_type", "record_attribute"}:
            raise HTTPException(404, "Not found")
        row = await self.host._get_model(db, kind, entity_id)
        if kind == "record_type":
            import app.modules.record.services.type_access as type_access

            await type_access.require_owner_access(db, row, user)
            row.is_active = 1 if active else 0
        else:
            row.payload = {**(row.payload or {}), "status": "active" if active else "inactive"}
        row.updated_by = await self.host.actor_officer_id(db, user)
        row.updated_at = utcnow()
        await db.flush()
        return await self.get_item(db, entity_id, user)

    async def soft_delete(self, db: AsyncSession, user: User, entity_id: str, expected) -> dict:
        kind = self.kind()
        if kind == "entity":
            return await self.host._soft_delete_entity(db, user, entity_id, expected)
        return await self.purge(db, user, entity_id, expected)

    async def purge(self, db: AsyncSession, user: User, entity_id: str, expected) -> dict:
        kind = self.kind()
        uid = uuid.UUID(entity_id)
        if kind == "entity":
            return await self.host._purge_entity(db, user, entity_id, expected)
        model = {"record_type": RecordType, "record_attribute": RecordAttribute}.get(kind)
        if not model:
            raise HTTPException(404, "Not found")
        row = await db.get(model, uid)
        if not row:
            raise HTTPException(404, "Not found")
        if kind == "record_type":
            import app.modules.record.services.type_access as type_access

            await type_access.require_owner_access(db, row, user)
        await db.delete(row)
        await db.flush()
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
        await db.flush()
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
        await db.flush()
        await db.refresh(row)
        return stamp(row)
