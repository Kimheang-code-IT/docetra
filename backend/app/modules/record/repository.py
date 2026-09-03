"""Session-bound persistence for Record-owned tables."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.record.model import Entity, Record, RecordDetail, RecordType, RecordTypePermission


class RecordRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record(self, record_id: uuid.UUID) -> Record | None:
        return await self.session.get(Record, record_id)

    async def record_type(self, record_type_id: uuid.UUID) -> RecordType | None:
        return await self.session.get(RecordType, record_type_id)

    async def type_by_code(self, code: str) -> RecordType | None:
        return await self.session.scalar(select(RecordType).where(RecordType.code == code))

    async def entity(self, resource: str, entity_id: uuid.UUID) -> Entity | None:
        return await self.session.scalar(
            select(Entity).where(Entity.id == entity_id, Entity.resource == resource)
        )

    async def entity_by_id(self, entity_id: uuid.UUID) -> Entity | None:
        return await self.session.get(Entity, entity_id)

    async def details(self, record_id: uuid.UUID) -> list[RecordDetail]:
        query = select(RecordDetail).where(RecordDetail.record_id == record_id)
        return list((await self.session.scalars(query)).all())

    async def permissions(self, record_type_id: uuid.UUID) -> list[RecordTypePermission]:
        query = select(RecordTypePermission).where(
            RecordTypePermission.record_type_id == record_type_id
        )
        return list((await self.session.scalars(query)).all())

    async def add(self, row) -> None:
        self.session.add(row)
        await self.session.flush()

    async def delete(self, row) -> None:
        await self.session.delete(row)
        await self.session.flush()


__all__ = ["RecordRepository"]
