from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Entity
from app.modules.record.services.stamp import entity_or_404, stamp


def resolved_schema(row: Entity) -> dict:
    payload = stamp(row)
    return {
        "recordType": payload,
        "tabs": payload.get("tabs", []),
        "fields": payload.get("fields") or payload.get("attributes", []),
        "workflowStages": payload.get("workflowStages", []),
        "version": row.version,
    }


async def schema_by_code(db: AsyncSession, code: str) -> dict:
    row = await db.scalar(select(Entity).where(Entity.resource == "record-types", Entity.payload["code"].as_string() == code))
    if not row:
        raise HTTPException(404, "Record type not found")
    return resolved_schema(row)


async def schema_by_id(db: AsyncSession, entity_id: str) -> dict:
    return resolved_schema(await entity_or_404(db, "record-types", entity_id))
