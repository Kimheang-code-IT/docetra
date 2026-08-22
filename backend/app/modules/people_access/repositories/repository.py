"""User / role repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.access import Permission, Role
from app.models.people import Officer, User
from app.shared import get_or_404


async def get_user(db: AsyncSession, user_id: str | uuid.UUID) -> User:
    return await get_or_404(db, User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await db.scalar(select(User).where(User.email == email.lower()))


async def get_role(db: AsyncSession, role_id: str | uuid.UUID) -> Role:
    return await get_or_404(db, Role, role_id)


async def list_roles(db: AsyncSession) -> list[Role]:
    return list((await db.scalars(select(Role).order_by(Role.updated_at.desc()))).all())


async def list_permissions(db: AsyncSession, role_id: uuid.UUID) -> list[str]:
    return list((await db.scalars(select(Permission.code).where(Permission.role_id == role_id, Permission.is_enable == 1))).all())


async def get_officer(db: AsyncSession, officer_id: str | uuid.UUID) -> Officer:
    return await get_or_404(db, Officer, officer_id)
