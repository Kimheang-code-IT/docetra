"""Storage-owned reporting read methods."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.modules.storage_integration.model import File


async def read_for_reporting(db, resource, ids, start, end) -> list[dict] | None:
    if resource != "file-uploads":
        return None
    filters = [File.status != "deleted"]
    if ids is not None:
        filters.append(File.id.in_(ids or [uuid.uuid4()]))
    if start:
        filters.append(File.created_at >= start)
    if end:
        filters.append(File.created_at <= end)
    rows = (await db.scalars(select(File).where(*filters).limit(10000))).all()
    return [
        {
            "id": str(row.id),
            "name": row.nam,
            "objectKey": row.path,
            "sizeBytes": row.file_size,
            "mimeType": row.mime_type,
            "status": row.status,
        }
        for row in rows
    ]


async def search_for_reporting(db, pattern: str, limit: int) -> list[dict]:
    rows = (await db.scalars(
        select(File)
        .where(File.status != "deleted", File.nam.ilike(pattern))
        .order_by(File.updated_at.desc())
        .limit(limit)
    )).all()
    return [
        {"resource": "file-uploads", "id": str(row.id), "title": row.nam or str(row.id), "description": row.nam, "updatedAt": row.updated_at}
        for row in rows
    ]
