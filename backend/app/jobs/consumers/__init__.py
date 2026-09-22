import json
import logging
import uuid
from datetime import datetime, timezone
from html import escape as html_escape

import aio_pika

from app.core.config import settings
from app.core.secrets import decrypt_value
from app.db import SessionLocal
from app.modules.record.model import Entity, Record
from app.platform.audit.model import AuditLog

log = logging.getLogger(__name__)

_MEETING_TEMPLATE = "[{{record_type}}] {{record_number}}\n{{record_title}}"


async def handle_security_email(payload: dict) -> None:
    if payload.get("kind") != "password_reset":
        return
    from app.integrations.email import send_password_reset
    from app.integrations.telegram import send_message
    from app.modules.admin_config.service import runtime

    async with SessionLocal() as db:
        config = await runtime.load_app_config(db)
        smtp = runtime.email_smtp(config)
        telegram = runtime.telegram_meeting(config)

    email = str(payload.get("email") or "")
    code = decrypt_value(str(payload.get("code") or ""))

    try:
        await send_password_reset(email, code, smtp=smtp)
    except Exception:  # noqa: BLE001 - never let email failure drop the Telegram fallback
        log.exception("Password reset email delivery failed for %s", email)

    # Telegram fallback/second channel: same account, so the reset code reaches
    # admins even when SMTP is not configured.
    if telegram.get("enabled") and telegram.get("botToken"):
        text = (
            "🔐 <b>Password Reset</b>\n"
            "\n"
            f"👤 {html_escape(email)}\n"
            f"🔑 Code: <code>{html_escape(code)}</code>\n"
            "⏳ Expires in 15 minutes\n"
            "\n"
            f"🕒 <i>Sent {datetime.now(timezone.utc):%d/%m/%Y %H:%M} UTC</i>"
        )
        for destination in telegram.get("destinations") or []:
            chat_id = str(destination.get("chatId") or "")
            if not destination.get("enabled", True) or not chat_id:
                continue
            # Reset codes are sensitive: private chats only, never groups/channels.
            if chat_id.startswith("-"):
                continue
            try:
                await send_message(telegram["botToken"], chat_id, text)
            except Exception:  # noqa: BLE001 - one bad chat must not block the rest
                log.exception("Password reset Telegram delivery failed chat_id=%s", chat_id)


def _format_meeting_alert(meeting, rendered: str, kind: str, details: dict) -> str:
    """Professional, icon-led Telegram message with clear spacing."""
    if str(kind).startswith("reminder"):
        header = "🔔 <b>Meeting Reminder</b>"
    elif str(kind).startswith("start"):
        header = "▶️ <b>Meeting Starting</b>"
    elif str(kind).startswith("end"):
        header = "⏹️ <b>Meeting Ended</b>"
    else:
        header = "📅 <b>Meeting Update</b>"
    lines = [header, "", html_escape(rendered)]
    meta: list[str] = []
    if meeting.record_time:
        meta.append(f"🕒 {meeting.record_time.astimezone(timezone.utc):%d/%m/%Y %H:%M}")
    location = details.get("location") if isinstance(details, dict) else None
    if location:
        meta.append(f"📍 {html_escape(str(location))}")
    if meeting.stage:
        meta.append(f"🏷️ {html_escape(str(meeting.stage))}")
    if meta:
        lines += ["", "   ·   ".join(meta)]
    lines += ["", f"🕒 <i>Sent {datetime.now(timezone.utc):%d/%m/%Y %H:%M} UTC</i>", "🏛️ <i>Docetra</i>"]
    return "\n".join(lines)


async def handle_meeting_message(payload: dict, routing: str) -> None:
    from app.modules.admin_config.service import runtime
    from app.integrations.telegram import send_meeting_alert
    from app.modules.record.service import details_as_dict

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
        rendered = runtime.render_telegram_template(
            _MEETING_TEMPLATE,
            title=title,
            kind=kind,
            record_type="meeting",
            record_number=str(details.get("recordNumber") or details.get("meetingNumber") or ""),
        )
        text = _format_meeting_alert(meeting, rendered, kind, details)
        destinations = bot["destinations"] or []
        for destination in destinations:
            if destination.get("enabled", True) and destination.get("chatId"):
                try:
                    await send_meeting_alert(str(destination["chatId"]), text, bot=bot)
                except Exception:  # noqa: BLE001 - one bad chat must not block the rest
                    log.exception("Telegram meeting alert failed chat_id=%s", destination.get("chatId"))
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
            from app.modules.storage_integration.service import drive_sync

            await drive_sync.run_sync_job(db, job)
            await db.commit()
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
        elif routing == "export.execute":
            from app.jobs.consumers.exports import handle_export_execute

            await handle_export_execute(payload)
