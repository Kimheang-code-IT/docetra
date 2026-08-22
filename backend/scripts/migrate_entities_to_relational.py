"""Idempotent migration: copy Entity JSONB rows into draft relational tables.

Usage:
  cd backend && python -m scripts.migrate_entities_to_relational
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.organization import Organization, OrganizationPurpose, OrganizationSector
from app.models.people import Officer
from app.models.record import Entity, Record
from app.models.storage import File
from app.modules.organization.domain.map import ORG_RESOURCES
from app.modules.record.domain.map import RECORD_RESOURCES
from app.modules.record.services.serializer import ensure_record_type, replace_details, apply_core_fields

log = logging.getLogger(__name__)


async def migrate() -> None:
    async with SessionLocal() as db:
        entities = (await db.scalars(select(Entity).where(Entity.status != "deleted"))).all()
        for row in entities:
            payload = dict(row.payload or {})
            if row.resource in RECORD_RESOURCES:
                code = RECORD_RESOURCES[row.resource]
                rtype = await ensure_record_type(db, code)
                existing = await db.get(Record, row.id)
                if existing:
                    continue
                record = Record(
                    id=row.id,
                    record_type_id=rtype.id,
                    record_type_code=code,
                    title=str(payload.get("title") or payload.get("name") or ""),
                    stage=row.stage,
                    lifecycle=row.status or "active",
                    record_time=row.record_time,
                    created_by=None,
                    updated_by=None,
                    version=row.version or 1,
                    archived_at=row.archived_at,
                    deleted_at=row.deleted_at,
                )
                apply_core_fields(record, payload, row.status or "active")
                db.add(record)
                await db.flush()
                await replace_details(db, record.id, payload, None)
            elif row.resource in ORG_RESOURCES:
                if await db.get(Organization, row.id):
                    continue
                db.add(Organization(
                    id=row.id,
                    nam=str(payload.get("name") or ""),
                    code=payload.get("code"),
                    organization_type=ORG_RESOURCES[row.resource],
                    parent_id=uuid.UUID(str(payload["parentId"])) if payload.get("parentId") else None,
                    is_active=0 if row.status == "inactive" else 1,
                    description=payload.get("description"),
                ))
            elif row.resource == "company-sectors":
                if await db.get(OrganizationSector, row.id):
                    continue
                db.add(OrganizationSector(id=row.id, nam=str(payload.get("name") or ""), is_active=1, description=payload.get("description")))
            elif row.resource == "company-purposes":
                if await db.get(OrganizationPurpose, row.id):
                    continue
                db.add(OrganizationPurpose(id=row.id, nam=str(payload.get("name") or ""), is_active=1, description=payload.get("description")))
            elif row.resource == "officers":
                if await db.get(Officer, row.id):
                    continue
                db.add(Officer(
                    id=row.id,
                    nam=str(payload.get("name") or ""),
                    email=payload.get("email"),
                    organization_id=uuid.UUID(str(payload["departmentId"])) if payload.get("departmentId") else None,
                    is_active=0 if row.status == "inactive" else 1,
                ))
            elif row.resource == "file-uploads":
                if await db.get(File, row.id):
                    continue
                db.add(File(
                    id=row.id,
                    nam=str(payload.get("name") or payload.get("fileName") or "file"),
                    path=str(payload.get("objectKey") or ""),
                    file_size=int(payload.get("sizeBytes") or 0),
                    mime_type=payload.get("mimeType"),
                    direct_url=payload.get("url"),
                    status="active" if row.status == "active" else "trash",
                    source_table="file-uploads",
                ))
        await db.commit()
        log.info("Migrated %s entity rows into relational tables", len(entities))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(migrate())
