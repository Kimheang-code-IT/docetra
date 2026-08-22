from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.secrets import mask_mapping, protect_mapping
from app.core.security import now_iso
from app.db import Entity, Outbox, User
from app.modules.record.services.stamp import entity_or_404, stamp


async def list_drive_files(db: AsyncSession, limit: int) -> tuple[list[dict], int]:
    rows = (await db.scalars(
        select(Entity).where(Entity.resource.in_(["drive-files", "google-drive-sync"]), Entity.status == "active").limit(min(200, limit))
    )).all()
    data = [stamp(row) for row in rows]
    return data, len(data)


async def create_drive_source(db: AsyncSession, body: dict, user: User) -> dict:
    if not body.get("folderId") and not settings.google_drive_folder_id:
        raise HTTPException(422, "folderId is required")
    row = Entity(
        resource="google-drive-sync",
        payload=protect_mapping({**body, "kind": "source", "syncStatus": "not_tested"}),
        status="active",
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {**stamp(row), **mask_mapping(row.payload or {})}


async def start_drive_sync(db: AsyncSession, source_id: str, user: User) -> dict:
    source = await entity_or_404(db, "google-drive-sync", source_id)
    if (source.payload or {}).get("kind") != "source":
        raise HTTPException(404, "Drive source not found")
    existing = await db.scalar(
        select(Entity).where(
            Entity.resource == "google-drive-sync",
            Entity.payload["kind"].as_string() == "job",
            Entity.payload["sourceId"].as_string() == source_id,
            Entity.payload["status"].as_string().in_(["queued", "processing"]),
        )
    )
    if existing:
        return stamp(existing)
    job = Entity(
        resource="google-drive-sync",
        payload={"kind": "job", "sourceId": source_id, "status": "queued", "attempts": 0, "createdAt": now_iso()},
        status="active",
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(job)
    await db.flush()
    db.add(Outbox(topic="drive.sync", payload={"jobId": str(job.id)}))
    await db.commit()
    await db.refresh(job)
    return stamp(job)


async def drive_sync_status(db: AsyncSession, job_id: str) -> dict:
    row = await entity_or_404(db, "google-drive-sync", job_id)
    if (row.payload or {}).get("kind") != "job":
        raise HTTPException(404, "Drive sync job not found")
    return stamp(row)
