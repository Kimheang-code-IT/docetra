from datetime import datetime, timezone
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.secrets import reveal_mapping
from app.db import Entity


async def sync_job(db: AsyncSession, job: Entity) -> int:
    payload = dict(job.payload or {})
    source_id = payload.get("sourceId")
    try:
        parsed_source_id = uuid.UUID(str(source_id)) if source_id else None
    except ValueError:
        parsed_source_id = None
    source = await db.get(Entity, parsed_source_id) if parsed_source_id else None
    source_payload = reveal_mapping(source.payload or {}) if source else {}
    token = str(source_payload.get("accessToken") or settings.google_drive_access_token)
    folder_id = str(source_payload.get("folderId") or settings.google_drive_folder_id)
    if not token or not folder_id:
        raise RuntimeError("Google Drive access token and folder ID are required")
    query = f"'{folder_id}' in parents and trashed = false"
    params = {
        "q": query,
        "pageSize": 1000,
        "fields": "files(id,name,mimeType,size,webViewLink,modifiedTime,createdTime,parents,md5Checksum)",
        "orderBy": "modifiedTime desc",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get("https://www.googleapis.com/drive/v3/files", params=params, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        files = response.json().get("files") or []
    for item in files:
        drive_id = str(item.get("id") or "")
        row = await db.scalar(select(Entity).where(Entity.resource == "drive-files", Entity.payload["driveFileId"].as_string() == drive_id))
        normalized = {
            "driveFileId": drive_id,
            "name": item.get("name"),
            "mimeType": item.get("mimeType"),
            "sizeBytes": int(item.get("size") or 0),
            "webViewLink": item.get("webViewLink"),
            "modifiedTime": item.get("modifiedTime"),
            "createdTime": item.get("createdTime"),
            "md5Checksum": item.get("md5Checksum"),
            "sourceId": str(source.id) if source else None,
            "syncedAt": datetime.now(timezone.utc).isoformat(),
        }
        if row:
            row.payload = normalized
        else:
            db.add(Entity(resource="drive-files", payload=normalized, status="active", created_by=job.created_by, updated_by=job.updated_by))
    payload.update({"status": "completed", "fileCount": len(files), "completedAt": datetime.now(timezone.utc).isoformat()})
    job.payload = payload
    if source:
        source.payload = {**(source.payload or {}), "lastSyncAt": datetime.now(timezone.utc).isoformat(), "syncStatus": "connected"}
    await db.commit()
    return len(files)
