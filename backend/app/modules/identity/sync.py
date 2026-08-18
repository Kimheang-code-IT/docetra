from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import Entity, MeetingSchedule, Officer, Organization, Record, Role

ORG_KINDS = {
    "departments": "department",
    "companies": "company",
    "company-purposes": "company_purpose",
    "company-sectors": "company_sector",
}
RECORD_KINDS = {
    "incoming-documents": "incoming_document",
    "outgoing-documents": "outgoing_document",
    "documents": "document",
    "master-list-requests": "master_list_request",
    "meeting-topics": "meeting_topic",
    "meeting-history": "meeting_history",
}


async def sync_domain_row(db: AsyncSession, row: Entity) -> None:
    payload = row.payload or {}
    now = datetime.now(timezone.utc)
    if row.resource == "roles":
        domain = await db.get(Role, row.id) or Role(id=row.id)
        domain.code = str(payload.get("code") or row.id)
        domain.name = str(payload.get("name") or domain.code)
        domain.status = row.status
        domain.permissions = list(payload.get("permissions") or [])
        domain.payload = payload
        domain.updated_at = now
        db.add(domain)
        return
    if row.resource in ORG_KINDS:
        domain = await db.get(Organization, row.id) or Organization(id=row.id)
        domain.kind = ORG_KINDS[row.resource]
        domain.code = payload.get("code")
        domain.name = str(payload.get("name") or payload.get("title") or row.id)
        domain.status = row.status
        domain.parent_id = payload.get("parentId")
        domain.payload = payload
        domain.updated_at = now
        db.add(domain)
        return
    if row.resource == "officers":
        domain = await db.get(Officer, row.id) or Officer(id=row.id)
        domain.name = str(payload.get("name") or row.id)
        domain.email = payload.get("email")
        domain.organization_id = payload.get("departmentId") or payload.get("organizationId")
        domain.status = row.status
        domain.payload = payload
        domain.updated_at = now
        db.add(domain)
        return
    if row.resource in RECORD_KINDS:
        domain = await db.get(Record, row.id) or Record(id=row.id)
        domain.kind = RECORD_KINDS[row.resource]
        domain.title = str(payload.get("title") or payload.get("name") or "")
        domain.status = row.status
        domain.stage = row.stage
        domain.record_time = row.record_time
        domain.details = payload.get("details") or {}
        domain.payload = payload
        domain.created_by = row.created_by
        domain.updated_at = now
        db.add(domain)
        if row.resource == "meeting-history":
            from app.modules.identity.schedules import upsert_meeting_jobs
            await upsert_meeting_jobs(db, row)


async def upsert_meeting_schedule(db: AsyncSession, row: Entity) -> None:
    if not row.record_time or row.status != "active":
        return
    key = f"meeting:{row.id}:start"
    existing = await db.scalar(select(MeetingSchedule).where(MeetingSchedule.job_key == key))
    if existing:
        existing.run_at = row.record_time
        existing.status = "scheduled"
        return
    db.add(MeetingSchedule(meeting_id=row.id, job_key=key, run_at=row.record_time, kind="start", status="scheduled"))
