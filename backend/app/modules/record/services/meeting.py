import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import now_iso
from app.db import User
from app.modules.record.services.stamp import entity_or_404, stamp


async def assign_topic(db: AsyncSession, meeting_id: str, body: dict) -> dict:
    row = await entity_or_404(db, "meeting-history", meeting_id)
    row.payload = {**row.payload, "topicId": body.get("topicId"), "topicTitle": body.get("topicTitle"), "sortOrder": body.get("sortOrder")}
    await db.commit()
    await db.refresh(row)
    return stamp(row)


async def reorder_meetings(db: AsyncSession, body: dict) -> dict:
    ids = body.get("orderedMeetingIds", [])
    for index, item_id in enumerate(ids):
        row = await entity_or_404(db, "meeting-history", item_id)
        row.payload = {**row.payload, "topicId": body.get("topicId"), "sortOrder": index}
    await db.commit()
    return {"topicId": body.get("topicId"), "orderedMeetingIds": ids}


async def link_drive_attachment(db: AsyncSession, meeting_id: str, body: dict) -> dict:
    row = await entity_or_404(db, "meeting-history", meeting_id)
    file = {
        "id": str(uuid.uuid4()),
        "name": body.get("displayName") or "Drive file",
        "mimeType": body.get("mimeType", "application/octet-stream"),
        "sizeBytes": body.get("sizeBytes", 0),
        "url": body.get("webViewLink"),
        "uploadedAt": now_iso(),
        "storageSource": "google_drive",
        "driveFileId": body.get("driveFileId"),
    }
    row.payload = {**row.payload, "attachments": [file, *row.payload.get("attachments", [])]}
    await db.commit()
    return file
