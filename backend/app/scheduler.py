import asyncio
import json
from datetime import datetime, timedelta, timezone
import aio_pika
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from app.core.config import settings
from app.db import Entity, MeetingSchedule, SessionLocal
from app.jobs.topology import EVENT_EXCHANGE

connection = None


async def publish(routing_key: str, payload: dict) -> None:
    global connection
    if not connection or connection.is_closed:
        connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel(publisher_confirms=True)
    exchange = await channel.declare_exchange(EVENT_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    await exchange.publish(
        aio_pika.Message(json.dumps(payload).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
        routing_key=routing_key,
    )


async def publish_tick() -> None:
    await publish("scheduler.reconcile", {"occurredAt": datetime.now(timezone.utc).isoformat(), "kind": "scheduler.reconcile"})


async def due_meeting_reminders() -> None:
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(minutes=15)
    async with SessionLocal() as db:
        schedules = (await db.scalars(
            select(MeetingSchedule).where(
                MeetingSchedule.status == "scheduled",
                MeetingSchedule.run_at >= now,
                MeetingSchedule.run_at <= horizon,
            )
        )).all()
        for job in schedules:
            await publish("meeting.reminder.due", {"meetingId": str(job.meeting_id), "at": job.run_at.isoformat(), "kind": job.kind})
            job.status = "queued"
        if not schedules:
            rows = (await db.scalars(
                select(Entity).where(
                    Entity.resource == "meeting-history",
                    Entity.status == "active",
                    Entity.record_time.is_not(None),
                    Entity.record_time >= now,
                    Entity.record_time <= horizon,
                )
            )).all()
            for row in rows:
                await publish("meeting.reminder.due", {"meetingId": str(row.id), "at": row.record_time.isoformat() if row.record_time else None})
        await db.commit()


async def cleanup_expired_exports() -> None:
    now = datetime.now(timezone.utc)
    async with SessionLocal() as db:
        rows = (await db.scalars(select(Entity).where(Entity.resource == "export-jobs", Entity.payload["expiresAt"].as_string() < now.isoformat()))).all()
        from app.modules.storage_integration.storage import delete_object
        for row in rows:
            key = (row.payload or {}).get("objectKey")
            if key:
                try:
                    await delete_object(key)
                except Exception:
                    continue
            await db.delete(row)
        await db.commit()


async def run() -> None:
    scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
    scheduler.add_job(publish_tick, "interval", minutes=15, id="reconcile", coalesce=True, max_instances=1)
    scheduler.add_job(due_meeting_reminders, "interval", minutes=1, id="meeting-reminders", coalesce=True, max_instances=1)
    scheduler.add_job(cleanup_expired_exports, "interval", hours=1, id="export-cleanup", coalesce=True, max_instances=1)
    scheduler.start()
    await publish_tick()
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        scheduler.shutdown(wait=False)
        if connection:
            await connection.close()

if __name__ == "__main__":
    asyncio.run(run())
