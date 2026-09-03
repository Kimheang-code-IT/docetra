"""Session-bound persistence for Storage Integration tables."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.storage_integration.model import File


class StorageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def file(self, file_id: uuid.UUID) -> File | None:
        return await self.session.get(File, file_id)

    async def add(self, row: File) -> None:
        self.session.add(row)
        await self.session.flush()

    async def delete(self, row: File) -> None:
        await self.session.delete(row)
        await self.session.flush()


__all__ = ["StorageRepository"]
