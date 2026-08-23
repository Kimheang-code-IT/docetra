"""Typed-table collection service — replaces Entity JSONB CRUD for frontend adapters."""

from __future__ import annotations

import math
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy import String, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.authorization import creator_only
from app.core.datetime import iso_utc, parse_instant, utcnow
from app.core.errors import DomainError
from app.models.access import Role
from app.models.audit import AuditLog
from app.models.organization import Organization, OrganizationPurpose, OrganizationSector
from app.models.people import Officer, User
from app.models.record import Entity, Record, RecordAttribute, RecordType
from app.models.storage import File
from app.modules.people_access.services.identity import normalize_identity_payload, parse_role_level, strip_secrets
import app.modules.organization.services.service as org_service
import app.modules.people_access.services.people as people
import app.modules.record.services.serializer as record_ser
from app.modules.organization.domain.map import (
    LEGACY_ORG_RESOURCES,
    ORG_RESOURCES,
    ORG_TYPE_TO_RESOURCE,
    db_org_type_for,
    is_valid_org_type,
)
from app.modules.record.domain.map import (
    LIFECYCLE_TO_STATUS,
    RECORD_RESOURCES,
    TYPE_CODE_TO_RESOURCE,
    is_valid_type_code,
)
import app.modules.organization.services.record_links as record_org_links

# Portal / jobs bags still stored as Entity JSONB until dedicated tables exist.
ENTITY_RESOURCES = {
    "google-drive-sync",
    "drive-files",
    "storage-providers",
    "export-jobs",
}
from app.modules.record.services.stamp import assert_writable, entity_or_404, stamp, apply_side_effects, audit
from app.modules.storage_integration.services.storage import delete_object, put_bytes, safe_name
from app.modules.storage_integration.services.upload_validation import detect_upload_type
from app.core.datetime import extract_record_time
from app.shared.pagination import parse_limit


class CollectionService:
    def __init__(
        self,
        resource: str | None = None,
        *,
        type_code: str | None = None,
        org_type: str | None = None,
    ):
        self.org_type: str | None = None
        if type_code:
            if not is_valid_type_code(type_code):
                from fastapi import HTTPException
                raise HTTPException(404, "Record type not found")
            self.type_code = type_code
            self.org_type = None
            self.resource = TYPE_CODE_TO_RESOURCE.get(type_code) or f"type:{type_code}"
        elif org_type:
            if not is_valid_org_type(org_type):
                from fastapi import HTTPException
                raise HTTPException(404, "Organization type not found")
            self.org_type = org_type
            self.type_code = None
            self.resource = ORG_TYPE_TO_RESOURCE.get(org_type) or f"org:{org_type}"
        elif resource:
            self.resource = resource
            self.type_code = RECORD_RESOURCES.get(resource)
            self.org_type = LEGACY_ORG_RESOURCES.get(resource)
        else:
            raise ValueError("CollectionService requires resource, type_code, or org_type")

    def kind(self) -> str:
        if self.type_code or self.resource in RECORD_RESOURCES:
            return "record"
        if self.org_type or self.resource in ORG_RESOURCES:
            return "organization"
        if self.resource == "sectors":
            return "sector"
        if self.resource == "purposes":
            return "purpose"
        if self.resource == "officers":
            return "officer"
        if self.resource == "roles":
            return "role"
        if self.resource == "users":
            return "user"
        if self.resource == "record-types":
            return "record_type"
        if self.resource == "record-attributes":
            return "record_attribute"
        if self.resource == "file-uploads":
            return "file"
        if self.resource in {"record-logs", "portal-logs", "system-logs"}:
            return "audit"
        if self.resource in ENTITY_RESOURCES:
            return "entity"
        return "unsupported"

    def resolve_type_code(self) -> str:
        if self.type_code:
            return self.type_code
        code = RECORD_RESOURCES.get(self.resource or "")
        if not code:
            from fastapi import HTTPException
            raise HTTPException(404, "Record type not found")
        return code

    def resolve_db_org_type(self) -> str:
        if self.org_type:
            return db_org_type_for(self.org_type)
        if self.resource in ORG_RESOURCES:
            return ORG_RESOURCES[self.resource]
        from fastapi import HTTPException
        raise HTTPException(404, "Organization type not found")

    async def get_record_row_or_404(self, db: AsyncSession, entity_id: str) -> Record:
        try:
            uid = uuid.UUID(str(entity_id))
        except ValueError as exc:
            raise HTTPException(404, "Not found") from exc
        row = await db.get(Record, uid)
        if not row or row.record_type_code != self.resolve_type_code():
            raise HTTPException(404, "Not found")
        return row

    async def get_org_row_or_404(self, db: AsyncSession, entity_id: str) -> Organization:
        row = await org_service.get_org(db, entity_id)
        if row.organization_type != self.resolve_db_org_type():
            raise HTTPException(404, "Not found")
        return row

    async def actor_officer_id(self, db: AsyncSession, user: User) -> uuid.UUID | None:
        officer = await people.ensure_officer_for_user(db, user)
        return officer.id

    async def list_items(self, db: AsyncSession, user: User, params: dict) -> dict:
        kind = self.kind()
        page = max(1, int(params.get("page") or 1))
        import app.modules.admin_config.services.runtime as runtime

        config = await runtime.load_app_config(db)
        default_limit = runtime.general_defaults(config)["defaultPageSize"]
        limit = parse_limit(params.get("limit"), default=default_limit)
        q = params.get("q") or params.get("search")
        status = params.get("status")

        if kind == "record":
            type_code = self.resolve_type_code()
            filters = [Record.record_type_code == type_code]
            if not status or status in {"all", "all-status"}:
                filters.append(Record.lifecycle.notin_(("archived", "deleted")))
            else:
                filters.append(Record.lifecycle.in_([p for p in status.split(",") if p]))
            if await creator_only(db, user, self.resource):
                officer_id = await self.actor_officer_id(db, user)
                filters.append(Record.created_by == officer_id)
            stage = params.get("stage")
            if stage and stage not in {"all"}:
                stages = [p for p in stage.split(",") if p]
                if "__empty__" in stages:
                    filters.append(Record.stage.is_(None))
                elif stages:
                    filters.append(Record.stage.in_(stages))
            if q:
                filters.append(Record.title.ilike(f"%{q}%"))
            start = parse_instant(params.get("startDate"))
            end = parse_instant(params.get("endDate"), end_of_day=True)
            if start:
                filters.append(Record.record_time >= start)
            if end:
                filters.append(Record.record_time <= end)
            total = await db.scalar(select(func.count()).select_from(Record).where(*filters)) or 0
            sort = params.get("sort") or "-updatedAt"
            desc = sort.startswith("-")
            key = sort.lstrip("-")
            column = {"createdAt": Record.created_at, "updatedAt": Record.updated_at, "recordTime": Record.record_time, "meetingDate": Record.record_time}.get(key, Record.updated_at)
            rows = (await db.scalars(select(Record).where(*filters).order_by(column.desc() if desc else column.asc(), Record.id).offset((page - 1) * limit).limit(limit))).all()
            data = [await record_ser.serialize_record(db, row) for row in rows]
            return {"data": data, "meta": {"page": page, "limit": limit, "total": total, "totalPages": max(1, math.ceil(total / limit))}}

        if kind == "organization":
            org_type = self.resolve_db_org_type()
            filters = [Organization.organization_type == org_type]
            if not status or status in {"all", "all-status"}:
                filters.append(Organization.is_active == 1)
            elif "inactive" in (status or ""):
                filters.append(Organization.is_active == 0)
            else:
                filters.append(Organization.is_active == 1)
            if q:
                filters.append(Organization.nam.ilike(f"%{q}%"))
            parent_id = params.get("parentId")
            if parent_id:
                try:
                    filters.append(Organization.parent_id == uuid.UUID(str(parent_id)))
                except ValueError:
                    filters.append(Organization.id == None)  # noqa: E711 — force empty
            elif str(params.get("rootsOnly") or "").lower() in {"1", "true", "yes"}:
                filters.append(Organization.parent_id.is_(None))
            total = await db.scalar(select(func.count()).select_from(Organization).where(*filters)) or 0
            rows = (await db.scalars(select(Organization).where(*filters).order_by(Organization.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
            return {"data": [org_service.org_to_payload(row) for row in rows], "meta": {"page": page, "limit": limit, "total": total, "totalPages": max(1, math.ceil(total / limit))}}

        if kind == "sector":
            filters = []
            if not status or status in {"all", "all-status"}:
                filters.append(OrganizationSector.is_active == 1)
            if q:
                filters.append(OrganizationSector.nam.ilike(f"%{q}%"))
            rows = (await db.scalars(select(OrganizationSector).where(*filters).order_by(OrganizationSector.updated_at.desc()).limit(limit))).all() if filters else (await db.scalars(select(OrganizationSector).order_by(OrganizationSector.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
            total = len(rows)
            return {"data": [org_service.sector_to_payload(row) for row in rows], "meta": {"page": page, "limit": limit, "total": total, "totalPages": 1}}

        if kind == "purpose":
            rows = (await db.scalars(select(OrganizationPurpose).order_by(OrganizationPurpose.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
            return {"data": [org_service.purpose_to_payload(row) for row in rows], "meta": {"page": page, "limit": limit, "total": len(rows), "totalPages": 1}}

        if kind == "officer":
            filters = []
            if not status or status in {"all", "all-status"}:
                filters.append(Officer.is_active == 1)
            if q:
                filters.append(Officer.nam.ilike(f"%{q}%"))
            stmt = select(Officer)
            if filters:
                stmt = stmt.where(*filters)
            total = await db.scalar(select(func.count()).select_from(Officer).where(*filters)) if filters else await db.scalar(select(func.count()).select_from(Officer))
            rows = (await db.scalars(stmt.order_by(Officer.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
            return {"data": [people.officer_to_payload(row) for row in rows], "meta": {"page": page, "limit": limit, "total": total or 0, "totalPages": max(1, math.ceil((total or 0) / limit))}}

        if kind == "role":
            rows = (await db.scalars(select(Role).order_by(Role.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
            data = []
            for row in rows:
                perms = await people.permissions_for_role_id(db, row.id)
                data.append(people.role_to_payload(row, perms))
            return {"data": data, "meta": {"page": page, "limit": limit, "total": len(data), "totalPages": 1}}

        if kind == "user":
            rows = (await db.scalars(select(User).order_by(User.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
            return {"data": [people.user_to_payload(row) for row in rows], "meta": {"page": page, "limit": limit, "total": len(rows), "totalPages": 1}}

        if kind == "record_type":
            rows = (await db.scalars(select(RecordType).order_by(RecordType.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
            data = [{
                "id": str(row.id), "code": row.code, "name": row.nam or row.code, "description": row.description,
                "status": "active" if row.is_active else "inactive", "deletable": bool(row.deletable),
                **(row.payload or {}), "createdAt": iso_utc(row.created_at), "updatedAt": iso_utc(row.updated_at), "version": 1,
            } for row in rows]
            return {"data": data, "meta": {"page": page, "limit": limit, "total": len(data), "totalPages": 1}}

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
            source = {"portal-logs": "portal", "system-logs": "system"}.get(self.resource, "record")
            filters = [AuditLog.source_log == source] if source != "record" else [AuditLog.source_log.in_(("record", "api", "unknown"))]
            if self.resource == "record-logs":
                from app.modules.record.domain.map import TYPE_CODE_TO_RESOURCE, TYPE_UI_DEFAULTS
                doc_codes = [code for code, meta in TYPE_UI_DEFAULTS.items() if meta.get("uiSurface") == "document"]
                doc_resources = [TYPE_CODE_TO_RESOURCE[c] for c in doc_codes if c in TYPE_CODE_TO_RESOURCE]
                allowed = set(doc_codes) | set(doc_resources) | {r.replace("-", "_") for r in doc_resources}
                # Soft filter: keep unmatched legacy rows (null/unknown table) so logs stay usable.
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
            return await self._list_entity(db, user, params, page, limit, q, status)

        raise DomainError("UNSUPPORTED", f"Resource {self.resource} is not mapped", 501)

    async def get_item(self, db: AsyncSession, entity_id: str) -> dict:
        kind = self.kind()
        try:
            uid = uuid.UUID(entity_id)
        except ValueError as exc:
            raise HTTPException(404, "Not found") from exc
        if kind == "record":
            row = await self.get_record_row_or_404(db, entity_id)
            return await record_ser.serialize_record(db, row)
        if kind == "organization":
            row = await self.get_org_row_or_404(db, entity_id)
            return org_service.org_to_payload(row)
        if kind == "officer":
            row = await db.get(Officer, uid)
            if not row:
                raise HTTPException(404, "Not found")
            return people.officer_to_payload(row)
        if kind == "role":
            row = await db.get(Role, uid)
            if not row:
                raise HTTPException(404, "Not found")
            return people.role_to_payload(row, await people.permissions_for_role_id(db, row.id))
        if kind == "user":
            row = await db.get(User, uid)
            if not row:
                raise HTTPException(404, "Not found")
            return people.user_to_payload(row)
        if kind == "record_type":
            row = await db.get(RecordType, uid)
            if not row:
                raise HTTPException(404, "Not found")
            return {"id": str(row.id), "code": row.code, "name": row.nam or row.code, "description": row.description, "status": "active" if row.is_active else "inactive", **(row.payload or {}), "version": 1, "createdAt": iso_utc(row.created_at), "updatedAt": iso_utc(row.updated_at)}
        if kind == "record_attribute":
            row = await db.get(RecordAttribute, uid)
            if not row:
                raise HTTPException(404, "Not found")
            return {"id": str(row.id), "code": row.code, "name": row.nam or row.code, "dataType": row.data_type, **(row.payload or {}), "version": 1, "createdAt": iso_utc(row.created_at), "updatedAt": iso_utc(row.updated_at)}
        if kind == "file":
            row = await db.get(File, uid)
            if not row:
                raise HTTPException(404, "Not found")
            return {"id": str(row.id), "name": row.nam, "objectKey": row.path, "sizeBytes": row.file_size, "mimeType": row.mime_type, "url": row.direct_url or f"/api/v2/files/{row.id}", "status": row.status, "version": 1}
        if kind == "sector":
            row = await db.get(OrganizationSector, uid)
            if not row:
                raise HTTPException(404, "Not found")
            return org_service.sector_to_payload(row)
        if kind == "purpose":
            row = await db.get(OrganizationPurpose, uid)
            if not row:
                raise HTTPException(404, "Not found")
            return org_service.purpose_to_payload(row)
        if kind == "entity":
            return stamp(await entity_or_404(db, self.resource, entity_id))
        raise HTTPException(404, "Not found")

    async def create(self, db: AsyncSession, user: User, payload: dict, raw_payload: dict | None = None) -> dict:
        await assert_writable(db, self.resource)
        officer_id = await self.actor_officer_id(db, user)
        kind = self.kind()
        raw = raw_payload or payload

        if kind == "record":
            type_code = self.resolve_type_code()
            rtype = await record_ser.ensure_record_type(db, type_code, officer_id)
            row_id = uuid.uuid4()
            lifecycle = str(payload.pop("status", "active") or "active")
            stage = payload.pop("stage", None)
            row = Record(
                id=row_id,
                record_type_id=rtype.id,
                record_type_code=type_code,
                title=str(payload.get("title") or payload.get("name") or ""),
                stage=stage,
                lifecycle=lifecycle,
                status=LIFECYCLE_TO_STATUS.get(lifecycle, 1),
                created_by=officer_id,
                updated_by=officer_id,
            )
            record_ser.apply_core_fields(row, payload, lifecycle)
            db.add(row)
            await db.flush()
            await record_ser.replace_details(db, row.id, payload, officer_id)
            if type_code == "meeting_history":
                from app.modules.record.services.meeting_schedules import upsert_meeting_jobs

                await upsert_meeting_jobs(db, row, payload)
            await record_org_links.sync_record_organizations(db, row.id, payload, officer_id)
            db.add(AuditLog(created_by=officer_id, action_code="created", table_name="record", row_id=row.id, message=f"{user.name} created this record", source_log="record"))
            await db.commit()
            await db.refresh(row)
            return await record_ser.serialize_record(db, row)

        if kind == "organization":
            db_type = self.resolve_db_org_type()
            is_company = db_type == "company"
            parent = payload.get("parentId")
            if is_company and parent:
                # Companies do not use department hierarchy.
                parent = None
            await org_service.validate_org_parent(db, None, parent, organization_type=db_type if not is_company else None)
            sector_id, purpose_id = await org_service.resolve_sector_purpose_ids(db, payload, require_company=is_company)
            lvl = 1
            if not is_company:
                lvl = await org_service.resolve_org_level(db, parent)
            row = Organization(
                nam=str(payload.get("name") or ""),
                code=payload.get("code"),
                description=payload.get("description"),
                organization_type=db_type,
                parent_id=uuid.UUID(str(parent)) if parent else None,
                sector_id=sector_id,
                organization_purpose_id=purpose_id,
                lvl=lvl,
                tax_id=payload.get("taxId"),
                address=payload.get("address"),
                email=payload.get("email"),
                phone=payload.get("phone"),
                logo_url=payload.get("logoUrl"),
                is_active=0 if payload.get("status") == "inactive" else 1,
                created_by=officer_id,
                updated_by=officer_id,
            )
            db.add(row)
            await db.commit()
            await db.refresh(row)
            return org_service.org_to_payload(row)

        if kind == "officer":
            row = Officer(
                nam=str(payload.get("name") or ""),
                email=payload.get("email"),
                organization_id=uuid.UUID(str(payload["organizationId"])) if payload.get("organizationId") or payload.get("departmentId") else None,
                role_id=uuid.UUID(str(payload["roleId"])) if payload.get("roleId") else None,
                is_active=0 if payload.get("status") == "inactive" else 1,
                profile_url=payload.get("profileUrl") or payload.get("avatar"),
                created_by=officer_id,
                updated_by=officer_id,
            )
            if payload.get("departmentId") and not row.organization_id:
                row.organization_id = uuid.UUID(str(payload["departmentId"]))
            db.add(row)
            await db.commit()
            await db.refresh(row)
            return people.officer_to_payload(row)

        if kind == "role":
            data = await normalize_identity_payload(db, "roles", payload, actor=user)
            row = Role(
                nam=str(data.get("name") or data.get("code") or "Role"),
                description=data.get("description"),
                lvl=parse_role_level(data.get("lvl")),
                is_active=0 if data.get("status") == "inactive" else 1,
                created_by=officer_id,
                updated_by=officer_id,
            )
            db.add(row)
            await db.flush()
            await people.replace_role_permissions(db, row.id, list(data.get("permissions") or []))
            await db.commit()
            await db.refresh(row)
            return people.role_to_payload(row, await people.permissions_for_role_id(db, row.id))

        if kind == "user":
            data = await normalize_identity_payload(db, "users", payload, actor=user)
            from app.core.security import hash_password
            import secrets
            row = User(
                email=data["email"],
                name=data["name"],
                password_hash=hash_password(str(data.get("password") or secrets.token_urlsafe(18))),
                role=str(data.get("roleName") or "User"),
                role_id=uuid.UUID(str(data["roleId"])),
                permissions=list(data.get("_permissions") or []),
                active=data.get("status", "active") != "inactive",
                status=str(data.get("status") or "active"),
                created_by=officer_id,
                updated_by=officer_id,
            )
            db.add(row)
            await db.flush()
            await people.ensure_officer_for_user(db, row, row.role_id)
            await db.commit()
            await db.refresh(row)
            return people.user_to_payload(row)

        if kind == "record_type":
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
            await db.commit()
            await db.refresh(row)
            return await self.get_item(db, str(row.id))

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
            return await self.get_item(db, str(row.id))

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
            return await self.get_item(db, str(row.id))

        if kind == "sector":
            row = OrganizationSector(nam=str(payload.get("name") or ""), description=payload.get("description"), is_active=1, created_by=officer_id, updated_by=officer_id)
            if payload.get("parentId"):
                row.parent_id = uuid.UUID(str(payload["parentId"]))
            db.add(row)
            await db.commit()
            await db.refresh(row)
            return org_service.sector_to_payload(row)

        if kind == "purpose":
            row = OrganizationPurpose(nam=str(payload.get("name") or ""), description=payload.get("description"), is_active=1, created_by=officer_id, updated_by=officer_id)
            db.add(row)
            await db.commit()
            await db.refresh(row)
            return org_service.purpose_to_payload(row)

        if kind == "entity":
            return await self._create_entity(db, user, payload, raw)

        raise DomainError("UNSUPPORTED", f"Create not supported for {self.resource}", 501)

    async def update(self, db: AsyncSession, user: User, entity_id: str, body: dict) -> dict:
        await assert_writable(db, self.resource)
        officer_id = await self.actor_officer_id(db, user)
        kind = self.kind()
        current = await self.get_item(db, entity_id)
        expected = body.pop("version", None)
        if expected is not None and expected != current.get("version"):
            raise DomainError("VERSION_CONFLICT", "Record was changed by another user", 409)

        if kind == "record":
            row = await self.get_record_row_or_404(db, entity_id)
            raw = dict(body)
            lifecycle = str(raw["status"]) if "status" in raw else None
            record_ser.apply_core_fields(row, {**current, **body}, lifecycle)
            row.updated_by = officer_id
            row.updated_at = utcnow()
            row.version += 1
            await record_ser.replace_details(db, row.id, {**current, **body}, officer_id)
            if row.record_type_code == "meeting_history":
                from app.modules.record.services.meeting_schedules import upsert_meeting_jobs

                await upsert_meeting_jobs(db, row, {**current, **body})
            await record_org_links.sync_record_organizations(db, row.id, {**current, **body}, officer_id)
            await db.commit()
            return await record_ser.serialize_record(db, row)

        if kind == "organization":
            row = await self.get_org_row_or_404(db, entity_id)
            db_type = self.resolve_db_org_type()
            is_company = db_type == "company"
            parent_value = body.get("parentId", row.parent_id)
            if is_company:
                parent_value = None
            await org_service.validate_org_parent(
                db,
                row.id,
                parent_value,
                organization_type=db_type if not is_company else None,
            )
            if "name" in body:
                row.nam = str(body["name"])
            for attr, key in [("code", "code"), ("description", "description"), ("tax_id", "taxId"), ("address", "address"), ("email", "email"), ("phone", "phone"), ("logo_url", "logoUrl")]:
                if key in body:
                    setattr(row, attr, body[key])
            if "parentId" in body or not is_company:
                if is_company:
                    row.parent_id = None
                    row.lvl = 1
                else:
                    row.parent_id = uuid.UUID(str(parent_value)) if parent_value else None
                    row.lvl = await org_service.resolve_org_level(db, row.parent_id)
            if any(k in body for k in ("sectorId", "purposeId", "organizationPurposeId")):
                sector_id, purpose_id = await org_service.resolve_sector_purpose_ids(
                    db,
                    {
                        "sectorId": body.get("sectorId", row.sector_id),
                        "purposeId": body.get("purposeId", body.get("organizationPurposeId", row.organization_purpose_id)),
                    },
                    require_company=is_company,
                )
                row.sector_id = sector_id
                row.organization_purpose_id = purpose_id
            if "status" in body:
                row.is_active = 0 if body["status"] == "inactive" else 1
            row.updated_by = officer_id
            row.updated_at = utcnow()
            await db.commit()
            await db.refresh(row)
            return org_service.org_to_payload(row)

        if kind == "role":
            row = await db.get(Role, uuid.UUID(entity_id))
            if not row:
                raise HTTPException(404, "Not found")
            data = await normalize_identity_payload(db, "roles", {**current, **body}, row.id, actor=user)
            row.nam = str(data.get("name") or row.nam)
            row.description = data.get("description")
            if "status" in body:
                row.is_active = 0 if body["status"] == "inactive" else 1
            row.updated_by = officer_id
            await people.replace_role_permissions(db, row.id, list(data.get("permissions") or []))
            # refresh users with this role
            users = (await db.scalars(select(User).where(User.role_id == row.id))).all()
            perms = await people.permissions_for_role_id(db, row.id)
            for account in users:
                account.permissions = perms
                account.role = row.nam
            await db.commit()
            return people.role_to_payload(row, perms)

        if kind == "user":
            row = await db.get(User, uuid.UUID(entity_id))
            if not row:
                raise HTTPException(404, "Not found")
            data = await normalize_identity_payload(db, "users", {**current, **body}, row.id, actor=user)
            row.name = data["name"]
            row.email = data["email"]
            if data.get("roleId"):
                row.role_id = uuid.UUID(str(data["roleId"]))
                row.role = str(data.get("roleName") or row.role)
                if data.get("_permissions") is not None:
                    row.permissions = list(data["_permissions"])
            if data.get("password"):
                from app.core.security import hash_password
                row.password_hash = hash_password(str(data["password"]))
            if "status" in body:
                row.status = str(body["status"])
                row.active = body["status"] != "inactive"
            row.updated_by = officer_id
            row.version += 1
            await people.ensure_officer_for_user(db, row, row.role_id)
            await db.commit()
            return people.user_to_payload(row)

        if kind == "officer":
            row = await db.get(Officer, uuid.UUID(entity_id))
            if "name" in body:
                row.nam = str(body["name"])
            if "email" in body:
                row.email = body["email"]
            if "organizationId" in body or "departmentId" in body:
                raw = body.get("organizationId") or body.get("departmentId")
                row.organization_id = uuid.UUID(str(raw)) if raw else None
            if "status" in body:
                row.is_active = 0 if body["status"] == "inactive" else 1
            row.updated_by = officer_id
            await db.commit()
            return people.officer_to_payload(row)

        # generic get-after-patch for config types
        if kind in {"record_type", "record_attribute", "file", "sector", "purpose"}:
            row = await self._get_model(db, kind, entity_id)
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
                elif kind == "sector" and key == "name":
                    row.nam = str(value)
                elif kind == "purpose" and key == "name":
                    row.nam = str(value)
            row.updated_by = officer_id
            row.updated_at = utcnow()
            await db.commit()
            return await self.get_item(db, entity_id)

        if kind == "entity":
            return await self._update_entity(db, user, entity_id, body)

        raise DomainError("UNSUPPORTED", f"Update not supported for {self.resource}", 501)

    async def _get_model(self, db, kind, entity_id):
        uid = uuid.UUID(entity_id)
        mapping = {
            "record_type": RecordType,
            "record_attribute": RecordAttribute,
            "file": File,
            "sector": OrganizationSector,
            "purpose": OrganizationPurpose,
        }
        row = await db.get(mapping[kind], uid)
        if not row:
            raise HTTPException(404, "Not found")
        return row

    async def soft_delete(self, db: AsyncSession, user: User, entity_id: str) -> dict:
        await assert_writable(db, self.resource)
        kind = self.kind()
        if kind == "record":
            row = await self.get_record_row_or_404(db, entity_id)
            row.lifecycle = "deleted"
            row.status = 0
            row.deleted_at = utcnow()
            row.version += 1
            await db.commit()
            return {"id": entity_id}
        if kind == "organization":
            row = await self.get_org_row_or_404(db, entity_id)
            row.is_active = 0
            await db.commit()
            return {"id": entity_id}
        if kind == "role":
            row = await db.get(Role, uuid.UUID(entity_id))
            if not row:
                raise HTTPException(404, "Not found")
            row.is_active = 0
            await db.commit()
            return {"id": entity_id}
        if kind == "user":
            row = await db.get(User, uuid.UUID(entity_id))
            if not row:
                raise HTTPException(404, "Not found")
            row.active = False
            row.status = "deleted"
            await db.commit()
            return {"id": entity_id}
        if kind == "file":
            row = await db.get(File, uuid.UUID(entity_id))
            if not row:
                raise HTTPException(404, "Not found")
            row.status = "trash"
            await db.commit()
            return {"id": entity_id}
        if kind == "entity":
            return await self._soft_delete_entity(db, user, entity_id)
        return await self.purge(db, user, entity_id)

    async def purge(self, db: AsyncSession, user: User, entity_id: str) -> dict:
        await assert_writable(db, self.resource)
        kind = self.kind()
        uid = uuid.UUID(entity_id)
        if kind == "user" and uid == user.id:
            raise DomainError("CONFLICT", "You cannot purge your own account", 409)
        if kind == "role":
            assigned = await db.scalar(select(func.count()).select_from(User).where(User.role_id == uid))
            if assigned:
                raise DomainError("CONFLICT", f"Role is assigned to {assigned} users", 409)
        model = {
            "record": Record, "organization": Organization, "officer": Officer, "role": Role,
            "user": User, "record_type": RecordType, "record_attribute": RecordAttribute,
            "file": File, "sector": OrganizationSector, "purpose": OrganizationPurpose,
        }.get(kind)
        if kind == "entity":
            return await self._purge_entity(db, user, entity_id)
        if kind == "record":
            row = await self.get_record_row_or_404(db, entity_id)
            await db.delete(row)
            await db.commit()
            return {"id": entity_id}
        if kind == "organization":
            row = await self.get_org_row_or_404(db, entity_id)
            await db.delete(row)
            await db.commit()
            return {"id": entity_id}
        if not model:
            raise HTTPException(404, "Not found")
        row = await db.get(model, uid)
        if not row:
            raise HTTPException(404, "Not found")
        if kind == "file" and getattr(row, "path", None):
            await delete_object(row.path)
        if kind == "user":
            officer = await db.scalar(select(Officer).where(Officer.auth_id == uid))
            if officer:
                await db.delete(officer)
        await db.delete(row)
        await db.commit()
        return {"id": entity_id}

    async def lifecycle(self, db: AsyncSession, user: User, entity_id: str, status: str) -> dict:
        await assert_writable(db, self.resource)
        if self.kind() == "record":
            row = await self.get_record_row_or_404(db, entity_id)
            record_ser.apply_core_fields(row, {}, status)
            row.version += 1
            row.updated_at = utcnow()
            await db.commit()
            return await record_ser.serialize_record(db, row)
        if self.kind() == "entity":
            row = await entity_or_404(db, self.resource, entity_id)
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
        body = {"status": status}
        return await self.update(db, user, entity_id, body)

    async def set_stage(self, db: AsyncSession, user: User, entity_id: str, stage: Any) -> dict:
        await assert_writable(db, self.resource)
        kind = self.kind()
        if kind == "entity":
            row = await entity_or_404(db, self.resource, entity_id)
            row.stage = stage
            row.version += 1
            await audit(db, row, user, "transitioned", f"{user.name} changed the stage")
            await db.commit()
            await db.refresh(row)
            return stamp(row)
        if kind != "record":
            raise HTTPException(404, "Not found")
        row = await self.get_record_row_or_404(db, entity_id)
        row.stage = stage
        row.version += 1
        await db.commit()
        return await record_ser.serialize_record(db, row)

    async def create_upload(self, db: AsyncSession, user: User, request) -> dict:
        await assert_writable(db, self.resource)
        officer_id = await self.actor_officer_id(db, user)
        row_id = uuid.uuid4()
        form = await request.form()
        upload = next((value for value in form.values() if isinstance(value, StarletteUploadFile)), None)
        payload = {key: str(value) for key, value in form.items() if not isinstance(value, StarletteUploadFile)}
        if upload:
            content = await upload.read()
            filename = safe_name(upload.filename or "file")
            extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            import app.modules.admin_config.services.runtime as runtime

            policy = runtime.upload_policy(await runtime.load_app_config(db))
            if extension not in policy["allowedUploadExtensions"]:
                raise HTTPException(415, "File extension is not allowed")
            if len(content) > policy["maxUploadSizeMb"] * 1024 * 1024:
                raise HTTPException(413, "File exceeds the configured upload limit")
            detected = detect_upload_type(content, extension)
            object_key = f"{self.resource}/{row_id}/{filename}"
            await put_bytes(object_key, content, detected)
            payload.update({"fileName": filename, "name": filename, "mimeType": detected, "sizeBytes": len(content), "objectKey": object_key, "url": f"/api/v2/files/{row_id}", "status": "ready"})
        if self.kind() == "file":
            row = File(
                id=row_id,
                nam=str(payload.get("name") or "file"),
                path=str(payload.get("objectKey") or ""),
                file_size=int(payload.get("sizeBytes") or 0),
                mime_type=payload.get("mimeType"),
                storage_type="s3",
                direct_url=payload.get("url"),
                source_table="file-uploads",
                status="active",
                created_by=officer_id,
                updated_by=officer_id,
            )
            db.add(row)
            await db.commit()
            return await self.get_item(db, str(row.id))
        if self.kind() == "entity":
            payload = {**payload, "id": str(row_id)}
            return await self._create_entity(db, user, payload, payload, row_id=row_id)
        return await self.create(db, user, payload, payload)

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
        await db.commit()
        await db.refresh(row)
        return stamp(row)

    async def _update_entity(self, db, user, entity_id, body):
        row = await entity_or_404(db, self.resource, entity_id)
        expected = body.pop("version", None)
        if expected is not None and expected != row.version:
            raise DomainError("VERSION_CONFLICT", "Record was changed by another user", 409)
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
        await db.commit()
        await db.refresh(row)
        return stamp(row)

    async def _soft_delete_entity(self, db, user, entity_id):
        row = await entity_or_404(db, self.resource, entity_id)
        row.status = "deleted"
        row.deleted_at = utcnow()
        row.version += 1
        await apply_side_effects(db, row)
        await audit(db, row, user, "deleted", f"{user.name} deleted this record")
        await db.commit()
        return {"id": entity_id}

    async def _purge_entity(self, db, user, entity_id):
        row = await entity_or_404(db, self.resource, entity_id)
        if (row.payload or {}).get("objectKey"):
            await delete_object(row.payload["objectKey"])
        await db.delete(row)
        await db.commit()
        return {"id": entity_id}
