from sqlalchemy import String, cast, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Entity


async def search_mentions(db: AsyncSession, q: str, mention_type: str, limit: int) -> list[dict]:
    resource = {"officer": "officers", "department": "departments", "company": "companies"}.get(mention_type, "officers")
    rows = (await db.scalars(
        select(Entity).where(
            Entity.resource == resource,
            Entity.status == "active",
            cast(Entity.payload, String).ilike(f"%{q}%"),
        ).limit(min(limit, 50))
    )).all()
    return [{"id": str(row.id), "label": (row.payload or {}).get("name") or (row.payload or {}).get("title") or str(row.id), "type": mention_type} for row in rows]
