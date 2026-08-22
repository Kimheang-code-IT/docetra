"""Record repository — typed record queries."""

from __future__ import annotations

import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.record import Record, RecordDetail, RecordType
from app.shared import get_or_404, page_meta, paginate, parse_limit


async def get_record(db: AsyncSession, record_id: str | uuid.UUID) -> Record:
    return await get_or_404(db, Record, record_id)


async def list_by_type(
    db: AsyncSession,
    type_code: str,
    *,
    page: int = 1,
    limit: int = 20,
    filters: list | None = None,
    order_by=None,
) -> tuple[list[Record], int]:
    stmt: Select = select(Record).where(Record.record_type_code == type_code)
    for clause in filters or []:
        stmt = stmt.where(clause)
    if order_by is not None:
        stmt = stmt.order_by(order_by, Record.id)
    else:
        stmt = stmt.order_by(Record.updated_at.desc(), Record.id)
    rows, total = await paginate(db, stmt, page=page, limit=limit)
    return list(rows), total


async def ensure_type(db: AsyncSession, code: str, actor_officer_id: uuid.UUID | None = None) -> RecordType:
    row = await db.scalar(select(RecordType).where(RecordType.code == code))
    if row:
        return row
    row = RecordType(code=code, nam=code.replace("_", " ").title(), is_active=1, created_by=actor_officer_id, updated_by=actor_officer_id)
    db.add(row)
    await db.flush()
    return row


async def list_details(db: AsyncSession, record_id: uuid.UUID) -> list[RecordDetail]:
    return list((await db.scalars(select(RecordDetail).where(RecordDetail.record_id == record_id))).all())
