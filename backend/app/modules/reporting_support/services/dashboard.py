from datetime import datetime, timedelta, timezone

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import iso_utc
from app.core.frontend_contract import DASHBOARD_KPIS, RECORD_RESOURCES, user_can_view_resource
from app.models.people import User
from app.models.record import Record
from app.modules.record.domain.map import RECORD_RESOURCES as RECORD_TYPE_BY_RESOURCE
from app.modules.record.services.serializer import details_as_dict

STAGE_TYPE_CODES = tuple(RECORD_TYPE_BY_RESOURCE[r] for r in RECORD_RESOURCES if r in RECORD_TYPE_BY_RESOURCE)


async def build_dashboard_summary(db: AsyncSession, user: User) -> dict:
    now = datetime.now(timezone.utc)
    updated_at = iso_utc(now)

    grouped = (
        await db.execute(
            select(Record.record_type_code, func.count())
            .where(Record.lifecycle.notin_(("archived", "deleted")))
            .group_by(Record.record_type_code)
        )
    ).all()
    counts_by_code = dict(grouped)

    kpis = []
    for resource, label_key, href in DASHBOARD_KPIS:
        if not user_can_view_resource(user, resource):
            continue
        code = RECORD_TYPE_BY_RESOURCE.get(resource)
        kpis.append({
            "id": resource,
            "labelKey": label_key,
            "value": counts_by_code.get(code, 0) if code else 0,
            "href": href,
            "updatedAt": updated_at,
        })

    stage_filters = [
        Record.record_type_code.in_(STAGE_TYPE_CODES),
        Record.lifecycle.notin_(("archived", "deleted")),
        Record.stage.is_not(None),
        Record.stage != "",
    ]
    stage_rows = (
        await db.execute(select(Record.stage, func.count()).where(*stage_filters).group_by(Record.stage))
    ).all()
    work_by_stage = [{"stage": str(stage), "count": count} for stage, count in stage_rows if stage]

    horizon = now - timedelta(days=365)
    time_filters = [
        Record.record_type_code.in_(STAGE_TYPE_CODES),
        Record.lifecycle.notin_(("archived", "deleted")),
        Record.record_time.is_not(None),
        Record.record_time >= horizon,
    ]
    # One labeled expression: repeating date_trunc() binds 'day' separately and
    # PostgreSQL then rejects GROUP BY (column record_time must appear in GROUP BY).
    day = cast(Record.record_time, Date).label("day")
    time_rows = (
        await db.execute(
            select(day, func.count())
            .where(*time_filters)
            .group_by(day)
            .order_by(day)
        )
    ).all()
    records_over_time = [
        {"date": bucket.isoformat(), "count": count}
        for bucket, count in time_rows
        if bucket is not None
    ]

    events = []
    if user_can_view_resource(user, "meeting-history"):
        meeting_rows = (
            await db.scalars(
                select(Record)
                .where(
                    Record.record_type_code == "meeting_history",
                    Record.lifecycle == "active",
                    Record.record_time.is_not(None),
                    Record.record_time >= now - timedelta(days=30),
                    Record.record_time <= now + timedelta(days=90),
                )
                .order_by(Record.record_time.asc())
                .limit(40)
            )
        ).all()
        for row in meeting_rows:
            details = await details_as_dict(db, row.id)
            title = row.title or str(row.id)
            start = iso_utc(row.record_time)
            if not start:
                continue
            duration = int(details.get("durationMinutes") or 60)
            end_at = row.record_time + timedelta(minutes=max(duration, 1)) if row.record_time else None
            events.append({
                "id": str(row.id),
                "title": title,
                "start": start,
                "end": iso_utc(end_at) if end_at else None,
                "allDay": False,
                "color": "primary",
                "type": "meeting",
                "href": f"/meetings/history/{row.id}",
                "location": details.get("location"),
            })

    return {
        "kpis": kpis,
        "workByStage": work_by_stage,
        "recordsOverTime": records_over_time,
        "events": events,
    }
