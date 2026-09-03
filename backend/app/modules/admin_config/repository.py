"""Session-bound persistence for Admin Config tables."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin_config.model import AppSetting, Setting


class AdminConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_setting(self, setting_id: uuid.UUID) -> Setting | None:
        return await self.session.get(Setting, setting_id)

    async def settings(self, *, setting_type: str | None = None) -> list[Setting]:
        query = select(Setting)
        if setting_type:
            query = query.where(Setting.setting_type == setting_type)
        return list((await self.session.scalars(query.order_by(Setting.updated_at.desc()))).all())

    async def app_setting(self, key: str) -> AppSetting | None:
        return await self.session.get(AppSetting, key)

    async def add(self, row: Setting | AppSetting) -> None:
        self.session.add(row)
        await self.session.flush()


__all__ = ["AdminConfigRepository"]
