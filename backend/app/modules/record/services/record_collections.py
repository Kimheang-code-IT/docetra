"""Typed record application service — unified Record table collections."""

from __future__ import annotations

import math
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authorization import creator_only
from app.core.datetime import parse_instant, utcnow
from app.models.audit import AuditLog
from app.models.people import User
from app.models.record import Record
from app.modules.record.domain.map import LIFECYCLE_TO_STATUS
import app.modules.organization.services.record_links as record_org_links
import app.modules.record.services.serializer as record_ser


class RecordApplicationService:
    def __init__(self, host):
        self.host = host

    async def list_items(self, db: AsyncSession, user: User, params: dict, page: int, limit: int, q, status) -> dict:
        type_code = self.host.resolve_type_code()
        filters = [Record.record_type_code == type_code]
        if not status or status in {"all", "all-status"}:
            filters.append(Record.lifecycle.notin_(("archived", "deleted")))
        else:
            filters.append(Record.lifecycle.in_([p for p in status.split(",") if p]))
        if await creator_only(db, user, self.host.resource):
            officer_id = await self.host.actor_officer_id(db, user)
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

    async def get_item(self, db: AsyncSession, entity_id: str) -> dict:
        row = await self.host.get_record_row_or_404(db, entity_id)
        return await record_ser.serialize_record(db, row)

    async def create(self, db: AsyncSession, user: User, payload: dict) -> dict:
        officer_id = await self.host.actor_officer_id(db, user)
        type_code = self.host.resolve_type_code()
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

    async def update(self, db: AsyncSession, user: User, entity_id: str, body: dict, current: dict) -> dict:
        officer_id = await self.host.actor_officer_id(db, user)
        row = await self.host.get_record_row_or_404(db, entity_id)
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

    async def soft_delete(self, db: AsyncSession, entity_id: str, expected) -> dict:
        row = await self.host.get_record_row_or_404(db, entity_id)
        self.host._assert_version(row.version, expected)
        row.lifecycle = "deleted"
        row.status = 0
        row.deleted_at = utcnow()
        row.version += 1
        await db.commit()
        return {"id": entity_id}

    async def purge(self, db: AsyncSession, entity_id: str, expected) -> dict:
        row = await self.host.get_record_row_or_404(db, entity_id)
        self.host._assert_version(row.version, expected)
        await db.delete(row)
        await db.commit()
        return {"id": entity_id}

    async def lifecycle(self, db: AsyncSession, entity_id: str, status: str, expected) -> dict:
        row = await self.host.get_record_row_or_404(db, entity_id)
        self.host._assert_version(row.version, expected)
        record_ser.apply_core_fields(row, {}, status)
        row.version += 1
        row.updated_at = utcnow()
        await db.commit()
        return await record_ser.serialize_record(db, row)

    async def set_stage(self, db: AsyncSession, entity_id: str, stage: Any, expected) -> dict:
        row = await self.host.get_record_row_or_404(db, entity_id)
        self.host._assert_version(row.version, expected)
        row.stage = stage
        row.version += 1
        await db.commit()
        return await record_ser.serialize_record(db, row)
