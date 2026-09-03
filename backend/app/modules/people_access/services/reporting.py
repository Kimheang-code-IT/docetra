"""People Access-owned reporting read methods."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.people_access.model import Officer, Role, User
from app.modules.people_access.services import people


def _range(column, start: datetime | None, end: datetime | None) -> list:
    return ([column >= start] if start else []) + ([column <= end] if end else [])


async def read_for_reporting(db, resource, ids, start, end) -> list[dict] | None:
    if resource == "officers":
        model = Officer
        stmt = select(model).where(model.is_active != 0, *_range(model.created_at, start, end))
    elif resource == "roles":
        model = Role
        stmt = select(model).where(model.is_active != 0, *_range(model.created_at, start, end))
    elif resource == "users":
        model = User
        stmt = select(model).where(model.status != "deleted", *_range(model.created_at, start, end))
    else:
        return None
    if ids is not None:
        stmt = stmt.where(model.id.in_(ids or [uuid.uuid4()]))
    rows = (await db.scalars(stmt.limit(10000))).all()
    if resource == "officers":
        return [people.officer_to_payload(row) for row in rows]
    if resource == "users":
        return [people.user_to_payload(row) for row in rows]
    return [
        people.role_to_payload(row, await people.permissions_for_role_id(db, row.id))
        for row in rows
    ]


async def search_for_reporting(db, pattern: str, limit: int) -> list[dict]:
    rows = (await db.scalars(
        select(Officer)
        .where(Officer.is_active == 1, or_(Officer.nam.ilike(pattern), Officer.email.ilike(pattern)))
        .order_by(Officer.updated_at.desc())
        .limit(limit)
    )).all()
    return [
        {"resource": "officers", "id": str(row.id), "title": row.nam or str(row.id), "description": row.email or row.nam, "updatedAt": row.updated_at}
        for row in rows
    ]
