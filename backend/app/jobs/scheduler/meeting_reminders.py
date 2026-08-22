from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db import MeetingSchedule, SessionLocal
from app.jobs.publishers import publish
from app.models.record import Record


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
                select(Record).where(
                    Record.record_type_code == "meeting_history",
                    Record.lifecycle == "active",
                    Record.record_time.is_not(None),
                    Record.record_time >= now,
                    Record.record_time <= horizon,
                )
            )).all()
            for row in rows:
                await publish("meeting.reminder.due", {"meetingId": str(row.id), "at": row.record_time.isoformat() if row.record_time else None})
        await db.commit()
