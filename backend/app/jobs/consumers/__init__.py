import json
import logging
import uuid
from datetime import datetime, timezone

import aio_pika

from app.core.config import settings
from app.core.secrets import decrypt_value
from app.db import Entity, SessionLocal
from app.models.audit import AuditLog
from app.models.record import Record

log = logging.getLogger(__name__)


async def handle_security_email(payload: dict) -> None:
    if payload.get("kind") != "password_reset":
        return
    from app.integrations.email import send_password_reset

    await send_password_reset(str(payload.get("email") or ""), decrypt_value(str(payload.get("code") or "")))


async def handle_meeting_message(payload: dict, routing: str) -> None:
    import app.modules.admin_config.services.runtime as runtime
    from app.integrations.telegram import send_meeting_alert
    from app.modules.record.services.serializer import details_as_dict

    meeting_id = payload.get("meetingId") or payload.get("id")
    kind = payload.get("kind") or "reminder"
    async with SessionLocal() as db:
        meeting = None
        try:
            meeting = await db.get(Record, uuid.UUID(str(meeting_id)))
        except ValueError:
            pass
        if not meeting or meeting.record_type_code != "meeting_history" or meeting.lifecycle != "active":
            return
        details = await details_as_dict(db, meeting.id)
        title = meeting.title or str(meeting.id)
        config = await runtime.load_app_config(db)
        bot = runtime.telegram_meeting(config)
        text = runtime.render_telegram_template(
            bot["messageTemplate"],
            title=title,
            kind=kind,
            record_type="meeting",
            record_number=str(details.get("recordNumber") or details.get("meetingNumber") or ""),
        )
        destinations = bot["destinations"] or []
        for destination in destinations:
            if destination.get("enabled", True) and destination.get("verified", False) and destination.get("chatId"):
                await send_meeting_alert(str(destination["chatId"]), text, db=db)
        db.add(AuditLog(
            action_code=routing,
            table_name="meeting-history",
            row_id=meeting.id,
            message=text,
            detail_data={"location": details.get("location"), "kind": kind},
            source_log="portal",
            status_code="success",
        ))
        await db.commit()


async def handle_drive_sync(payload: dict) -> None:
    async with SessionLocal() as db:
        job = None
        try:
            job = await db.get(Entity, uuid.UUID(str(payload.get("jobId"))))
            if not job or (job.payload or {}).get("status") == "completed":
                return
            job.payload = {**(job.payload or {}), "status": "processing", "attempts": int((job.payload or {}).get("attempts") or 0) + 1}
            await db.commit()
            from app.integrations.google import sync_job

            await sync_job(db, job)
        except Exception as exc:
            if job:
                attempts = int((job.payload or {}).get("attempts") or 0)
                failed = attempts >= settings.job_max_retries
                job.payload = {**(job.payload or {}), "status": "failed" if failed else "queued", "error": str(exc)[:500], "completedAt": datetime.now(timezone.utc).isoformat() if failed else None}
                await db.commit()
                if failed:
                    return
            raise


async def handle_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=True):
        payload = json.loads(message.body.decode() or "{}")
        routing = message.routing_key or ""
        if routing == "notifications.email.security":
            await handle_security_email(payload)
        elif routing.startswith("meeting."):
            await handle_meeting_message(payload, routing)
        elif routing == "drive.sync":
            await handle_drive_sync(payload)
