"""File / setting / audit repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.configuration import Setting
from app.models.storage import File
from app.shared import get_or_404, paginate


async def get_file(db: AsyncSession, file_id: str | uuid.UUID) -> File:
    return await get_or_404(db, File, file_id)


async def list_files(db: AsyncSession, *, page: int = 1, limit: int = 20):
    stmt = select(File).where(File.status != "trash").order_by(File.updated_at.desc(), File.id)
    rows, total = await paginate(db, stmt, page=page, limit=limit)
    return list(rows), total


async def get_setting(db: AsyncSession, key_group: str, key: str) -> Setting | None:
    return await db.scalar(select(Setting).where(Setting.key_group == key_group, Setting.key == key))


async def list_settings(db: AsyncSession, key_group: str) -> list[Setting]:
    return list((await db.scalars(select(Setting).where(Setting.key_group == key_group).order_by(Setting.ordering))).all())


async def list_audit(db: AsyncSession, *, page: int = 1, limit: int = 20):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    rows, total = await paginate(db, stmt, page=page, limit=limit)
    return list(rows), total
