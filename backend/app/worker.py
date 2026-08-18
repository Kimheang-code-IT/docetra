import asyncio
import json
from datetime import datetime, timezone
import aio_pika
from sqlalchemy import select
from app.core.config import settings
from app.db import Entity, Outbox, SessionLocal
from app.jobs.topology import DEAD_LETTER_EXCHANGE, EVENT_EXCHANGE


async def publish_outbox(channel) -> None:
    exchange = await channel.declare_exchange(EVENT_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    async with SessionLocal() as db:
        rows = (await db.scalars(select(Outbox).where(Outbox.processed_at.is_(None)).order_by(Outbox.created_at).limit(100))).all()
        for row in rows:
            try:
                message = aio_pika.Message(json.dumps(row.payload).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT, message_id=str(row.id))
                await exchange.publish(message, routing_key=row.topic)
                row.processed_at = datetime.now(timezone.utc)
                row.attempts += 1
            except Exception:
                row.attempts += 1
                if row.attempts >= settings.job_max_retries:
                    row.processed_at = datetime.now(timezone.utc)
                    db.add(Entity(resource="system-logs", payload={"level": "error", "action": "outbox.failed", "outboxId": str(row.id), "topic": row.topic, "attempts": row.attempts, "occurredAt": datetime.now(timezone.utc).isoformat()}, status="active"))
        await db.commit()


async def complete_exports() -> None:
    async with SessionLocal() as db:
        rows = (await db.scalars(select(Entity).where(Entity.resource == "export-jobs", Entity.payload["status"].as_string() == "queued").limit(10))).all()
        for row in rows:
            try:
                row.payload={**(row.payload or {}),"status":"processing"}; await db.flush()
                from app.modules.reporting_support.exports import generate_export
                await generate_export(db,row)
            except Exception as exc:
                row.payload={**(row.payload or {}),"status":"failed","error":str(exc)[:500],"completedAt":datetime.now(timezone.utc).isoformat()}
        await db.commit()


async def handle_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=True):
        payload = json.loads(message.body.decode() or "{}")
        routing = message.routing_key or ""
        if routing == "notifications.email.security":
            if payload.get("kind") == "password_reset":
                from app.core.secrets import decrypt_value
                from app.modules.notifications.email import send_password_reset
                await send_password_reset(str(payload.get("email") or ""), decrypt_value(str(payload.get("code") or "")))
        elif routing.startswith("meeting."):
            from app.modules.notifications.telegram import send_meeting_alert
            meeting_id = payload.get("meetingId") or payload.get("id")
            kind = payload.get("kind") or "reminder"
            async with SessionLocal() as db:
                import uuid
                from app.core.secrets import reveal_mapping
                from app.db import AppSetting
                meeting = None
                try:
                    meeting = await db.get(Entity, uuid.UUID(str(meeting_id)))
                except ValueError:
                    pass
                if not meeting or meeting.resource != "meeting-history" or meeting.status != "active":
                    return
                meeting_payload = meeting.payload or {}
                title = str(meeting_payload.get("title") or meeting_payload.get("name") or meeting.id)
                text = f"Docetra meeting {kind}: {title}"
                config_row = await db.get(AppSetting, "app-config")
                telegram = reveal_mapping((((config_row.value if config_row else {}) or {}).get("telegram") or {}))
                destinations = telegram.get("destinations") or []
                for destination in destinations:
                    if destination.get("enabled", True) and destination.get("verified", False) and destination.get("chatId"):
                        await send_meeting_alert(str(destination["chatId"]), text)
                db.add(Entity(
                    resource="portal-logs",
                    payload={"summary": text, "action": routing, "occurredAt": datetime.now(timezone.utc).isoformat()},
                    status="active",
                ))
                await db.commit()
        elif routing == "drive.sync":
            async with SessionLocal() as db:
                try:
                    import uuid
                    job = await db.get(Entity, uuid.UUID(str(payload.get("jobId"))))
                    if not job or (job.payload or {}).get("status") == "completed":
                        return
                    job.payload = {**(job.payload or {}), "status": "processing", "attempts": int((job.payload or {}).get("attempts") or 0) + 1}
                    await db.commit()
                    from app.modules.storage_integration.google_drive import sync_job
                    await sync_job(db, job)
                except Exception as exc:
                    if 'job' in locals() and job:
                        attempts = int((job.payload or {}).get("attempts") or 0)
                        failed = attempts >= settings.job_max_retries
                        job.payload = {**(job.payload or {}), "status": "failed" if failed else "queued", "error": str(exc)[:500], "completedAt": datetime.now(timezone.utc).isoformat() if failed else None}
                        await db.commit()
                        if failed:
                            return
                    raise


async def consume(channel) -> None:
    await channel.declare_exchange(EVENT_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    await channel.declare_exchange(DEAD_LETTER_EXCHANGE, aio_pika.ExchangeType.FANOUT, durable=True)
    queue = await channel.declare_queue("docetra.work", durable=True, arguments={"x-dead-letter-exchange": DEAD_LETTER_EXCHANGE})
    await queue.bind(EVENT_EXCHANGE, routing_key="#")
    await queue.consume(handle_message)


async def run() -> None:
    while True:
        try:
            connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            async with connection:
                channel = await connection.channel(publisher_confirms=True)
                await channel.set_qos(prefetch_count=8)
                await consume(channel)
                while True:
                    await publish_outbox(channel)
                    await complete_exports()
                    await asyncio.sleep(2)
        except asyncio.CancelledError:
            raise
        except Exception:
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run())
