"""Typed record application service — unified Record table collections."""

from __future__ import annotations

import math
import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.record.services.creator_scope import creator_only
from app.core.datetime import parse_instant, utcnow, iso_utc
from app.core.privileged import is_unrestricted
from app.platform.audit.model import AuditLog
from typing import Any as User
from app.modules.record.model import Record, RecordType
from app.modules.record.domain.map import LIFECYCLE_TO_STATUS, merge_type_ui_payload
import app.modules.record.services.organization_links as record_org_links
import app.modules.record.services.serializer as record_ser
import app.modules.record.services.type_access as type_access


class RecordApplicationService:
    def __init__(self, host):
        self.host = host

    @staticmethod
    def _initial_stage(rtype: RecordType) -> str | None:
        merged = merge_type_ui_payload(rtype.code, dict(rtype.payload or {}))
        return next(
            (stage.get("code") for stage in merged.get("stages", []) if stage.get("isInitial")),
            None,
        )

    async def list_items(self, db: AsyncSession, user: User, params: dict, page: int, limit: int, q, status) -> dict:
        type_code = self.host.resolve_type_code()
        officer_id = await self.host.actor_officer_id(db, user)
        org_id = await type_access.actor_organization_id(db, user)
        unrestricted = is_unrestricted(user)
        rtype = await record_ser.resolve_or_ensure_type(
            db,
            type_code,
            officer_id,
            org_id,
            unrestricted=unrestricted,
        )
        if unrestricted:
            type_ids = list(
                (await db.scalars(select(RecordType.id).where(RecordType.code == type_code))).all()
            )
            if type_ids:
                filters = [or_(Record.record_type_id.in_(type_ids), Record.record_type_code == type_code)]
            else:
                filters = [Record.record_type_id == rtype.id]
        else:
            filters = [Record.record_type_id == rtype.id]
            if org_id:
                filters.append(await type_access.record_in_organization(db, org_id))
            else:
                # Unscoped accounts are constrained by role permissions rather
                # than an organization membership filter.
                pass
        if not status or status in {"all", "all-status"}:
            filters.append(Record.lifecycle.notin_(("archived", "deleted")))
        else:
            filters.append(Record.lifecycle.in_([p for p in status.split(",") if p]))
        if await creator_only(db, user, self.host.resource):
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
        data = await record_ser.serialize_records(db, rows)
        return {"data": data, "meta": {"page": page, "limit": limit, "total": total, "totalPages": max(1, math.ceil(total / limit))}}

    async def get_item(self, db: AsyncSession, user: User, entity_id: str) -> dict:
        row = await self.host.get_record_row_or_404(db, entity_id, user)
        return await record_ser.serialize_record(db, row)

    async def create(self, db: AsyncSession, user: User, payload: dict) -> dict:
        officer_id = await self.host.actor_officer_id(db, user)
        type_code = self.host.resolve_type_code()
        org_id = await type_access.actor_organization_id(db, user)
        rtype = await record_ser.resolve_or_ensure_type(
            db,
            type_code,
            officer_id,
            org_id,
            unrestricted=is_unrestricted(user),
        )
        row_id = uuid.uuid4()
        lifecycle = str(payload.pop("status", "active") or "active")
        stage = payload.pop("stage", None)
        if stage is None:
            stage = self._initial_stage(rtype)
        row = Record(
            id=row_id,
            record_type_id=rtype.id,
            record_type_code=rtype.code,
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
        await record_ser.replace_details(db, row.id, payload, officer_id, rtype.id)
        if type_code == "meeting_history":
            from app.modules.record.services.meeting_schedules import upsert_meeting_jobs

            await upsert_meeting_jobs(db, row, payload)
        await record_org_links.sync_record_organizations(db, row.id, payload, officer_id)
        db.add(AuditLog(created_by=officer_id, action_code="created", table_name="record", row_id=row.id, message=f"{user.name} created this record", source_log="record"))
        await db.flush()
        await db.refresh(row)
        return await record_ser.serialize_record(db, row)

    async def update(self, db: AsyncSession, user: User, entity_id: str, body: dict, current: dict) -> dict:
        officer_id = await self.host.actor_officer_id(db, user)
        row = await self.host.get_record_row_or_404(db, entity_id, user)
        raw = dict(body)
        lifecycle = str(raw["status"]) if "status" in raw else None
        record_ser.apply_core_fields(row, {**current, **body}, lifecycle)
        row.updated_by = officer_id
        row.updated_at = utcnow()
        row.version += 1
        await record_ser.replace_details(db, row.id, {**current, **body}, officer_id, row.record_type_id)
        if row.record_type_code == "meeting_history":
            from app.modules.record.services.meeting_schedules import upsert_meeting_jobs

            await upsert_meeting_jobs(db, row, {**current, **body})
        await record_org_links.sync_record_organizations(db, row.id, {**current, **body}, officer_id)
        await db.flush()
        return await record_ser.serialize_record(db, row)

    async def attach_file(self, db: AsyncSession, user: User, entity_id: str, file_payload: dict, expected=None) -> dict:
        """Attach one already-uploaded file reference to a record.

        ``file_payload`` is the public File result from Storage Integration —
        this service never touches storage internals. Existing attachments are
        preserved; re-attaching the same file id is idempotent.
        """
        file_id = str(file_payload.get("id") or "")
        if not file_id:
            raise HTTPException(422, "Attachment requires a file id")
        officer_id = await self.host.actor_officer_id(db, user)
        row = await self.host.get_record_row_or_404(db, entity_id, user)
        self.host._assert_version(row.version, expected)
        current = await record_ser.serialize_record(db, row)
        existing = [dict(item) for item in (current.get("attachments") or []) if isinstance(item, dict)]
        existing = [item for item in existing if str(item.get("id") or item.get("fileId") or "") != file_id]
        entry = {
            "id": file_id,
            "fileId": file_id,
            "name": str(file_payload.get("name") or file_payload.get("fileName") or "file"),
            "mimeType": file_payload.get("mimeType"),
            "sizeBytes": int(file_payload.get("sizeBytes") or 0),
            "objectKey": file_payload.get("objectKey"),
            "url": file_payload.get("url") or f"/api/v2/files/{file_id}",
            "uploadedAt": iso_utc(utcnow()),
        }
        existing.append(entry)
        updated = await self.update(db, user, entity_id, {"attachments": existing}, current)
        db.add(AuditLog(
            created_by=officer_id,
            action_code="attachment_added",
            table_name="record",
            row_id=row.id,
            message=f"{user.name} attached {entry['name']} to this record",
            source_log="record",
        ))
        await db.flush()
        return {"attachments": updated.get("attachments") or existing, "version": updated.get("version")}

    async def detach_file(self, db: AsyncSession, user: User, entity_id: str, file_id: str, expected=None) -> dict:
        """Remove a file reference from a record without deleting the shared File."""
        officer_id = await self.host.actor_officer_id(db, user)
        row = await self.host.get_record_row_or_404(db, entity_id, user)
        self.host._assert_version(row.version, expected)
        current = await record_ser.serialize_record(db, row)
        existing = [dict(item) for item in (current.get("attachments") or []) if isinstance(item, dict)]
        remaining = [item for item in existing if str(item.get("id") or item.get("fileId") or "") != str(file_id)]
        if len(remaining) == len(existing):
            raise HTTPException(404, "Attachment not found")
        updated = await self.update(db, user, entity_id, {"attachments": remaining}, current)
        db.add(AuditLog(
            created_by=officer_id,
            action_code="attachment_removed",
            table_name="record",
            row_id=row.id,
            message=f"{user.name} removed an attachment from this record",
            source_log="record",
        ))
        await db.flush()
        return {"attachments": updated.get("attachments") or remaining, "version": updated.get("version")}

    async def soft_delete(self, db: AsyncSession, user: User, entity_id: str, expected) -> dict:
        row = await self.host.get_record_row_or_404(db, entity_id, user)
        self.host._assert_version(row.version, expected)
        row.lifecycle = "deleted"
        row.status = 0
        row.deleted_at = utcnow()
        row.version += 1
        await db.flush()
        return {"id": entity_id}

    async def purge(self, db: AsyncSession, user: User, entity_id: str, expected) -> dict:
        row = await self.host.get_record_row_or_404(db, entity_id, user)
        self.host._assert_version(row.version, expected)
        await db.delete(row)
        await db.flush()
        return {"id": entity_id}

    async def lifecycle(self, db: AsyncSession, user: User, entity_id: str, status: str, expected) -> dict:
        row = await self.host.get_record_row_or_404(db, entity_id, user)
        self.host._assert_version(row.version, expected)
        record_ser.apply_core_fields(row, {}, status)
        row.version += 1
        row.updated_at = utcnow()
        await db.flush()
        return await record_ser.serialize_record(db, row)

    async def set_stage(self, db: AsyncSession, user: User, entity_id: str, stage: Any, expected) -> dict:
        row = await self.host.get_record_row_or_404(db, entity_id, user)
        self.host._assert_version(row.version, expected)
        row.stage = stage
        row.version += 1
        await db.flush()
        return await record_ser.serialize_record(db, row)
