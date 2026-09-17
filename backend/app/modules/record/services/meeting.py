import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import utcnow
from app.modules.record.model import Record, RecordType
from app.modules.record.services.serializer import apply_core_fields, replace_details, serialize_record


async def _meeting_history_row(db: AsyncSession, meeting_id: str) -> Record:
    try:
        uid = uuid.UUID(str(meeting_id))
    except ValueError as exc:
        raise HTTPException(404, "Not found") from exc
    row = await db.get(Record, uid)
    if not row:
        raise HTTPException(404, "Not found")
    if row.record_type_code == "meeting_history":
        return row
    if row.record_type_id:
        type_row = await db.get(RecordType, row.record_type_id)
        if type_row and type_row.code == "meeting_history":
            return row
    raise HTTPException(404, "Not found")


async def _resolve_topic(db: AsyncSession, topic_id: object) -> Record | None:
    """Validate a topicId for assign/reorder.

    Returns None for unassign (empty topicId). Rejects invalid ids (422),
    missing/deleted topics (404), non-topic records (422) and archived
    topics (422) so the browser cannot persist dangling assignments.
    """
    raw = str(topic_id or "").strip()
    if not raw:
        return None
    try:
        uid = uuid.UUID(raw)
    except ValueError as exc:
        raise HTTPException(422, "topicId must be a valid id") from exc
    row = await db.get(Record, uid)
    if not row or row.lifecycle == "deleted":
        raise HTTPException(404, "Meeting topic not found")
    code = row.record_type_code
    if code != "meeting_topic" and row.record_type_id:
        type_row = await db.get(RecordType, row.record_type_id)
        code = type_row.code if type_row else code
    if code != "meeting_topic":
        raise HTTPException(422, "topicId does not reference a meeting topic")
    if row.status != 1:
        raise HTTPException(422, "Meeting topic is archived")
    return row


async def _persist_topic_fields(db: AsyncSession, row: Record, body: dict) -> dict:
    current = await serialize_record(db, row)
    topic_id = body.get("topicId")
    merged = {
        **current,
        "topicId": topic_id or None,
        "topicTitle": body.get("topicTitle", current.get("topicTitle")),
        "sortOrder": body.get("sortOrder", current.get("sortOrder")),
    }
    if "topicId" in body and not topic_id:
        merged["topicTitle"] = None
        merged["sortOrder"] = None
    apply_core_fields(row, merged)
    row.updated_at = utcnow()
    row.version = int(row.version or 1) + 1
    await replace_details(db, row.id, merged, row.updated_by, row.record_type_id)
    await db.flush()
    await db.refresh(row)
    return await serialize_record(db, row)


async def assign_topic(db: AsyncSession, meeting_id: str, body: dict) -> dict:
    row = await _meeting_history_row(db, meeting_id)
    await _resolve_topic(db, body.get("topicId"))
    return await _persist_topic_fields(db, row, body)


async def reorder_meetings(db: AsyncSession, body: dict) -> dict:
    ids = body.get("orderedMeetingIds", [])
    topic_id = body.get("topicId")
    await _resolve_topic(db, topic_id)
    for index, item_id in enumerate(ids):
        row = await _meeting_history_row(db, item_id)
        await _persist_topic_fields(db, row, {
            "topicId": topic_id,
            "sortOrder": index,
        })
    return {"topicId": topic_id, "orderedMeetingIds": ids}


async def link_drive_attachment(db: AsyncSession, meeting_id: str, body: dict) -> dict:
    from app.core.security import now_iso

    row = await _meeting_history_row(db, meeting_id)
    drive_file_id = body.get("driveFileId")
    file = {
        "id": str(uuid.uuid4()),
        "name": body.get("displayName") or "Drive file",
        "mimeType": body.get("mimeType", "application/octet-stream"),
        "sizeBytes": int(body.get("sizeBytes") or 0),
        "url": body.get("webViewLink"),
        "uploadedAt": now_iso(),
        "storageSource": "google_drive",
        "driveFileId": drive_file_id,
    }
    current = await serialize_record(db, row)
    existing = [dict(item) for item in (current.get("attachments") or []) if isinstance(item, dict)]
    # Re-linking the same Drive file is idempotent.
    if drive_file_id:
        existing = [item for item in existing if item.get("driveFileId") != drive_file_id]
    merged = {**current, "attachments": [file, *existing]}
    apply_core_fields(row, merged)
    row.updated_at = utcnow()
    row.version = int(row.version or 1) + 1
    await replace_details(db, row.id, merged, row.updated_by, row.record_type_id)
    await db.flush()
    await db.refresh(row)
    return file
