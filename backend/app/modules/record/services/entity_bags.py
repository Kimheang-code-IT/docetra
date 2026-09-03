"""Public Record-owned operations for legacy Entity bags."""

from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import select

from app.modules.record.model import Entity
from app.modules.record.services.stamp import stamp


def _view(row: Entity) -> dict:
    return {"id": row.id, "resource": row.resource, "payload": dict(row.payload or {}), "status": row.status, "createdBy": row.created_by, "updatedBy": row.updated_by, "public": stamp(row)}


async def list_entities(db, resources: str | list[str], *, status: str | None = None, limit: int | None = None) -> list[dict]:
    values = [resources] if isinstance(resources, str) else list(resources)
    stmt = select(Entity).where(Entity.resource.in_(values))
    if status:
        stmt = stmt.where(Entity.status == status)
    if limit:
        stmt = stmt.limit(limit)
    return [_view(row) for row in (await db.scalars(stmt)).all()]


async def get_entity(db, resource: str, entity_id: str) -> dict:
    try:
        uid = uuid.UUID(entity_id)
    except ValueError as exc:
        raise HTTPException(404, "Not found") from exc
    row = await db.scalar(select(Entity).where(Entity.id == uid, Entity.resource == resource))
    if not row:
        raise HTTPException(404, "Not found")
    return _view(row)


async def create_entity(db, resource: str, payload: dict, *, status: str, created_by, updated_by) -> dict:
    row = Entity(resource=resource, payload=payload, status=status, created_by=created_by, updated_by=updated_by)
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return _view(row)


async def update_entity(db, resource: str, entity_id: str, *, payload: dict | None = None, status: str | None = None) -> dict:
    view = await get_entity(db, resource, entity_id)
    row = await db.get(Entity, view["id"])
    if payload is not None:
        row.payload = payload
    if status is not None:
        row.status = status
    await db.flush()
    await db.refresh(row)
    return _view(row)


async def delete_entity(db, resource: str, entity_id: str) -> None:
    view = await get_entity(db, resource, entity_id)
    row = await db.get(Entity, view["id"])
    await db.delete(row)
    await db.flush()


async def find_drive_job(db, source_id: str) -> dict | None:
    row = await db.scalar(
        select(Entity).where(
            Entity.resource == "google-drive-sync",
            Entity.payload["kind"].as_string() == "job",
            Entity.payload["sourceId"].as_string() == source_id,
            Entity.payload["status"].as_string().in_(["queued", "processing"]),
        )
    )
    return _view(row) if row else None


async def find_drive_file(db, drive_file_id: str) -> dict | None:
    row = await db.scalar(
        select(Entity).where(
            Entity.resource == "drive-files",
            Entity.payload["driveFileId"].as_string() == drive_file_id,
        )
    )
    return _view(row) if row else None


__all__ = ["create_entity", "delete_entity", "find_drive_file", "find_drive_job", "get_entity", "list_entities", "update_entity"]
