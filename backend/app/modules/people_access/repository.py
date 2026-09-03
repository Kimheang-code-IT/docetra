"""Session-bound persistence for People Access tables."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.people_access.model import Menu, Officer, OfficerIdentifier, Permission, Role, User


class PeopleAccessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def user(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def officer(self, officer_id: uuid.UUID) -> Officer | None:
        return await self.session.get(Officer, officer_id)

    async def officer_for_user(self, user_id: uuid.UUID) -> Officer | None:
        return await self.session.scalar(select(Officer).where(Officer.auth_id == user_id))

    async def role(self, role_id: uuid.UUID) -> Role | None:
        return await self.session.get(Role, role_id)

    async def add(self, row: User | Officer | OfficerIdentifier | Role | Menu | Permission) -> None:
        self.session.add(row)
        await self.session.flush()

    async def delete(self, row: User | Officer | OfficerIdentifier | Role | Menu | Permission) -> None:
        await self.session.delete(row)
        await self.session.flush()


__all__ = ["PeopleAccessRepository"]
