"""Record-owned reporting read methods."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import Date, cast, func, or_, select

from app.modules.record.domain.map import RECORD_RESOURCES
from app.modules.record.model import Entity, Record, RecordAttribute, RecordType
from app.modules.record.services import serializer
from app.core.datetime import iso_utc


async def read_for_reporting(db, resource, ids, start, end) -> list[dict] | None:
    if resource in RECORD_RESOURCES:
        filters = [
            Record.record_type_code == RECORD_RESOURCES[resource],
            Record.lifecycle != "deleted",
        ]
        if ids is not None:
            filters.append(Record.id.in_(ids or [uuid.uuid4()]))
        if start:
            filters.append(Record.record_time >= start)
        if end:
            filters.append(Record.record_time <= end)
        rows = (await db.scalars(select(Record).where(*filters).order_by(Record.updated_at.desc()).limit(10000))).all()
        return await serializer.serialize_records(db, rows)
    if resource in {"record-types", "record-attributes"}:
        model = RecordType if resource == "record-types" else RecordAttribute
        filters = []
        if ids is not None:
            filters.append(model.id.in_(ids or [uuid.uuid4()]))
        if start:
            filters.append(model.created_at >= start)
        if end:
            filters.append(model.created_at <= end)
        rows = (await db.scalars(select(model).where(*filters).limit(10000))).all()
        if resource == "record-types":
            return [{"id": str(r.id), "code": r.code, "name": r.nam or r.code, "description": r.description, **(r.payload or {})} for r in rows]
        return [{"id": str(r.id), "code": r.code, "name": r.nam or r.code, "dataType": r.data_type, **(r.payload or {})} for r in rows]
    if resource in {"google-drive-sync", "drive-files", "export-jobs"}:
        filters = [Entity.resource == resource, Entity.status != "deleted"]
        if ids is not None:
            filters.append(Entity.id.in_(ids or [uuid.uuid4()]))
        if start:
            filters.append(Entity.created_at >= start)
        if end:
            filters.append(Entity.created_at <= end)
        rows = (await db.scalars(select(Entity).where(*filters).order_by(Entity.updated_at.desc()).limit(10000))).all()
        return [{"id": str(row.id), **(row.payload or {}), "status": row.status, "stage": row.stage, "createdAt": row.created_at.isoformat() if row.created_at else None, "updatedAt": row.updated_at.isoformat() if row.updated_at else None} for row in rows]
    return None


async def search_for_reporting(db, pattern: str, limit: int) -> list[dict]:
    rows = (await db.scalars(
        select(Record)
        .where(
            Record.lifecycle.notin_(("archived", "deleted")),
            or_(Record.title.ilike(pattern), Record.record_content.ilike(pattern)),
        )
        .order_by(Record.updated_at.desc())
        .limit(limit)
    )).all()
    code_to_resource = {code: resource for resource, code in RECORD_RESOURCES.items()}
    return [
        {
            "resource": code_to_resource.get(row.record_type_code or ""),
            "id": str(row.id),
            "title": row.title or str(row.id),
            "description": row.record_content or row.title,
            "updatedAt": row.updated_at,
        }
        for row in rows
        if code_to_resource.get(row.record_type_code or "")
    ]


async def dashboard_read(db, now: datetime, stage_type_codes: tuple[str, ...]) -> dict:
    grouped = (await db.execute(
        select(Record.record_type_code, func.count())
        .where(Record.lifecycle.notin_(("archived", "deleted")))
        .group_by(Record.record_type_code)
    )).all()
    stage_rows = (await db.execute(
        select(Record.stage, func.count())
        .where(
            Record.record_type_code.in_(stage_type_codes),
            Record.lifecycle.notin_(("archived", "deleted")),
            Record.stage.is_not(None),
            Record.stage != "",
        )
        .group_by(Record.stage)
    )).all()
    day = cast(Record.record_time, Date).label("day")
    time_rows = (await db.execute(
        select(day, func.count())
        .where(
            Record.record_type_code.in_(stage_type_codes),
            Record.lifecycle.notin_(("archived", "deleted")),
            Record.record_time.is_not(None),
            Record.record_time >= now - timedelta(days=365),
        )
        .group_by(day)
        .order_by(day)
    )).all()
    meetings = (await db.scalars(
        select(Record)
        .where(
            Record.record_type_code == "meeting_history",
            Record.lifecycle == "active",
            Record.record_time.is_not(None),
            Record.record_time >= now - timedelta(days=30),
            Record.record_time <= now + timedelta(days=90),
        )
        .order_by(Record.record_time.asc())
        .limit(40)
    )).all()
    events = []
    for row in meetings:
        details = await serializer.details_as_dict(db, row.id)
        duration = int(details.get("durationMinutes") or 60)
        events.append({
            "id": str(row.id),
            "title": row.title or str(row.id),
            "start": iso_utc(row.record_time),
            "end": iso_utc(row.record_time + timedelta(minutes=max(duration, 1))) if row.record_time else None,
            "allDay": False,
            "color": "primary",
            "type": "meeting",
            "href": f"/meetings/history/{row.id}",
            "location": details.get("location"),
        })
    return {
        "countsByCode": dict(grouped),
        "workByStage": [{"stage": str(stage), "count": count} for stage, count in stage_rows if stage],
        "recordsOverTime": [{"date": bucket.isoformat(), "count": count} for bucket, count in time_rows if bucket],
        "events": [event for event in events if event["start"]],
    }
