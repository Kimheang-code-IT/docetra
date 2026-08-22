from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import MeetingSchedule
from app.models.record import Record
import app.modules.admin_config.services.runtime as runtime


async def upsert_meeting_jobs(db: AsyncSession, row: Record, details: dict | None = None) -> None:
    details = details or {}
    config = await runtime.load_app_config(db)
    reminders = runtime.meeting_reminders(config)
    await db.execute(
        MeetingSchedule.__table__.delete().where(MeetingSchedule.meeting_id == row.id, MeetingSchedule.status == "scheduled")
    )
    if row.lifecycle != "active":
        return
    start = row.record_time
    if not start:
        return
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    duration = int(details.get("durationMinutes") or 60)
    end = start + timedelta(minutes=max(duration, 1))
    jobs = [("start", start), ("end", end)]
    for offset in reminders["meetingReminderOffsetsMinutes"]:
        reminder_at = start - timedelta(minutes=int(offset))
        if reminder_at > datetime.now(timezone.utc):
            jobs.append((f"reminder_{offset}", reminder_at))
    rule = details.get("recurrence") or {}
    frequency = str(rule.get("frequency") or "").lower()
    if frequency in {"daily", "weekly"}:
        step = timedelta(days=1 if frequency == "daily" else 7)
        horizon = datetime.now(timezone.utc) + timedelta(days=reminders["meetingRecurrenceHorizonDays"])
        occurrence = start + step
        index = 1
        while occurrence <= horizon and index <= 52:
            jobs.append((f"start_occ_{index}", occurrence))
            occurrence += step
            index += 1
    for kind, run_at in jobs:
        key = f"meeting:{row.id}:{kind}"
        existing = await db.scalar(select(MeetingSchedule).where(MeetingSchedule.job_key == key))
        if existing:
            existing.run_at = run_at
            existing.status = "scheduled"
            existing.kind = kind.split("_")[0]
            continue
        db.add(MeetingSchedule(meeting_id=row.id, job_key=key, run_at=run_at, kind=kind.split("_")[0], status="scheduled"))
