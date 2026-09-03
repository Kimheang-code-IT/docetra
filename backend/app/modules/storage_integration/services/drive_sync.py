from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any as User

from app.core.config import settings
from app.core.secrets import mask_mapping, protect_mapping
from app.core.security import now_iso
from app.platform.messaging.model import Outbox
from app.modules.record.service import entity_bags


async def list_drive_files(db: AsyncSession, limit: int) -> tuple[list[dict], int]:
    rows = await entity_bags.list_entities(db, ["drive-files", "google-drive-sync"], status="active", limit=min(200, limit))
    data = [row["public"] for row in rows]
    return data, len(data)


async def create_drive_source(db: AsyncSession, body: dict, user: User) -> dict:
    if not body.get("folderId") and not settings.google_drive_folder_id:
        raise HTTPException(422, "folderId is required")
    row = await entity_bags.create_entity(
        db,
        "google-drive-sync",
        protect_mapping({**body, "kind": "source", "syncStatus": "not_tested"}),
        status="active",
        created_by=user.id,
        updated_by=user.id,
    )
    return {**row["public"], **mask_mapping(row["payload"])}


async def start_drive_sync(db: AsyncSession, source_id: str, user: User) -> dict:
    source = await entity_bags.get_entity(db, "google-drive-sync", source_id)
    if source["payload"].get("kind") != "source":
        raise HTTPException(404, "Drive source not found")
    existing = await entity_bags.find_drive_job(db, source_id)
    if existing:
        return existing["public"]
    job = await entity_bags.create_entity(
        db,
        "google-drive-sync",
        {"kind": "job", "sourceId": source_id, "status": "queued", "attempts": 0, "createdAt": now_iso()},
        status="active",
        created_by=user.id,
        updated_by=user.id,
    )
    db.add(Outbox(topic="drive.sync", payload={"jobId": str(job["id"])}))
    await db.flush()
    return job["public"]


async def drive_sync_status(db: AsyncSession, job_id: str) -> dict:
    row = await entity_bags.get_entity(db, "google-drive-sync", job_id)
    if row["payload"].get("kind") != "job":
        raise HTTPException(404, "Drive sync job not found")
    return row["public"]


async def run_sync_job(db: AsyncSession, job) -> int:
    """Execute a queued Drive sync job.

    ``job`` is the Record-owned job entity managed by the outbox consumer.
    This service owns the sync rules but never commits — the consumer owns
    the transaction.
    """
    from app.core.secrets import reveal_mapping
    from app.integrations.google import list_folder_files

    payload = dict(job.payload or {})
    source_id = payload.get("sourceId")
    source = None
    if source_id:
        try:
            source = await entity_bags.get_entity(db, "google-drive-sync", str(source_id))
        except HTTPException:
            source = None
    source_payload = reveal_mapping(source["payload"] or {}) if source else {}
    token = str(source_payload.get("accessToken") or settings.google_drive_access_token)
    folder_id = str(source_payload.get("folderId") or settings.google_drive_folder_id)
    if not token or not folder_id:
        raise RuntimeError("Google Drive access token and folder ID are required")
    files = await list_folder_files(token, folder_id)
    for item in files:
        drive_id = str(item.get("id") or "")
        row = await entity_bags.find_drive_file(db, drive_id)
        normalized = {
            "driveFileId": drive_id,
            "name": item.get("name"),
            "mimeType": item.get("mimeType"),
            "sizeBytes": int(item.get("size") or 0),
            "webViewLink": item.get("webViewLink"),
            "modifiedTime": item.get("modifiedTime"),
            "createdTime": item.get("createdTime"),
            "md5Checksum": item.get("md5Checksum"),
            "sourceId": str(source["id"]) if source else None,
            "syncedAt": datetime.now(timezone.utc).isoformat(),
        }
        if row:
            await entity_bags.update_entity(db, "drive-files", str(row["id"]), payload=normalized)
        else:
            await entity_bags.create_entity(
                db,
                "drive-files",
                normalized,
                status="active",
                created_by=job.created_by,
                updated_by=job.updated_by,
            )
    payload.update({"status": "completed", "fileCount": len(files), "completedAt": datetime.now(timezone.utc).isoformat()})
    job.payload = payload
    if source:
        await entity_bags.update_entity(
            db,
            "google-drive-sync",
            str(source["id"]),
            payload={**(source["payload"] or {}), "lastSyncAt": datetime.now(timezone.utc).isoformat(), "syncStatus": "connected"},
        )
    return len(files)
