"""Organization-owned collection facade, independent of Record internals."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.modules.organization.model import Organization, OrganizationPurpose, OrganizationSector
from typing import Any as User
from app.modules.admin_config.service import runtime
from app.modules.organization.domain.map import ORG_RESOURCES, ORG_TYPE_TO_RESOURCE, db_org_type_for
from app.modules.organization.services import service as org_service
from app.modules.organization.services.org_collections import OrganizationApplicationService
from app.shared.pagination import parse_limit


ActorResolver = Callable[[AsyncSession, User], Awaitable[uuid.UUID | None]]
CreatedHook = Callable[[AsyncSession, uuid.UUID, uuid.UUID | None], Awaitable[None]]


class OrganizationCollectionService:
    def __init__(
        self,
        *,
        resource: str | None = None,
        org_type: str | None = None,
        actor_resolver: ActorResolver,
        created_hook: CreatedHook | None = None,
    ) -> None:
        self.org_type = org_type
        self.resource = resource or ORG_TYPE_TO_RESOURCE.get(str(org_type))
        self._actor_resolver = actor_resolver
        self._created_hook = created_hook
        self.organizations = OrganizationApplicationService(self)

    def kind(self) -> str:
        if self.org_type or self.resource in ORG_RESOURCES:
            return "organization"
        if self.resource == "sectors":
            return "sector"
        if self.resource == "purposes":
            return "purpose"
        raise HTTPException(404, "Organization resource not found")

    def resolve_db_org_type(self) -> str:
        if self.org_type:
            return db_org_type_for(self.org_type)
        try:
            return ORG_RESOURCES[str(self.resource)]
        except KeyError as exc:
            raise HTTPException(404, "Organization type not found") from exc

    async def actor_officer_id(self, db: AsyncSession, user: User) -> uuid.UUID | None:
        return await self._actor_resolver(db, user)

    async def after_organization_created(
        self,
        db: AsyncSession,
        organization_id: uuid.UUID,
        actor_officer_id: uuid.UUID | None,
    ) -> None:
        if self._created_hook:
            await self._created_hook(db, organization_id, actor_officer_id)

    async def get_org_row_or_404(self, db: AsyncSession, entity_id: str) -> Organization:
        row = await org_service.get_org(db, entity_id)
        if row.organization_type != self.resolve_db_org_type():
            raise HTTPException(404, "Not found")
        return row

    async def _get_model(self, db: AsyncSession, kind: str, entity_id: str):
        model = {"sector": OrganizationSector, "purpose": OrganizationPurpose}[kind]
        try:
            row = await db.get(model, uuid.UUID(entity_id))
        except ValueError as exc:
            raise HTTPException(404, "Not found") from exc
        if not row:
            raise HTTPException(404, "Not found")
        return row

    async def _assert_writable(self, db: AsyncSession) -> None:
        general = runtime.general_defaults(await runtime.load_app_config(db))
        if general["maintenanceMode"]:
            raise DomainError("MAINTENANCE", "System is in maintenance mode", 503)
        if general["readOnlyMode"]:
            raise DomainError("READ_ONLY", "System is in read-only mode", 403)

    async def list_items(self, db: AsyncSession, user: User, params: dict) -> dict:
        page = max(1, int(params.get("page") or 1))
        general = runtime.general_defaults(await runtime.load_app_config(db))
        limit = parse_limit(params.get("limit"), default=general["defaultPageSize"])
        q = params.get("q") or params.get("search")
        return await self.organizations.list_items(
            db,
            user,
            params,
            page,
            limit,
            q,
            params.get("status"),
        )

    async def get_item(self, db: AsyncSession, entity_id: str, user=None) -> dict:
        return await self.organizations.get_item(db, entity_id)

    async def create(self, db: AsyncSession, user: User, payload: dict, raw_payload=None) -> dict:
        await self._assert_writable(db)
        return await self.organizations.create(db, user, payload)

    async def update(self, db: AsyncSession, user: User, entity_id: str, body: dict) -> dict:
        await self._assert_writable(db)
        body.pop("version", None)
        return await self.organizations.update(db, user, entity_id, body)

    async def soft_delete(self, db: AsyncSession, user: User, entity_id: str, body=None) -> dict:
        await self._assert_writable(db)
        return await self.organizations.soft_delete(db, entity_id)

    async def purge(self, db: AsyncSession, user: User, entity_id: str, body=None) -> dict:
        await self._assert_writable(db)
        return await self.organizations.purge(db, entity_id)

    async def lifecycle(
        self,
        db: AsyncSession,
        user: User,
        entity_id: str,
        status: str,
        body=None,
    ) -> dict:
        return await self.update(db, user, entity_id, {"status": status})

    async def set_stage(self, db, user, entity_id, stage, body=None):
        raise HTTPException(404, "Not found")


__all__ = ["OrganizationCollectionService"]
