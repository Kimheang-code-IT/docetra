"""Session-bound persistence for Organization tables."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organization.model import Organization, OrganizationPurpose, OrganizationSector


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, organization_id: uuid.UUID) -> Organization | None:
        return await self.session.get(Organization, organization_id)

    async def ids(self) -> list[uuid.UUID]:
        return list((await self.session.scalars(select(Organization.id))).all())

    async def sector(self, sector_id: uuid.UUID) -> OrganizationSector | None:
        return await self.session.get(OrganizationSector, sector_id)

    async def purpose(self, purpose_id: uuid.UUID) -> OrganizationPurpose | None:
        return await self.session.get(OrganizationPurpose, purpose_id)

    async def add(self, row: Organization | OrganizationSector | OrganizationPurpose) -> None:
        self.session.add(row)
        await self.session.flush()

    async def delete(self, row: Organization | OrganizationSector | OrganizationPurpose) -> None:
        await self.session.delete(row)
        await self.session.flush()


__all__ = ["OrganizationRepository"]
