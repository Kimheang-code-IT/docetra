"""People Access-owned collection facade."""

from __future__ import annotations

import uuid

from fastapi import HTTPException

from app.core.concurrency import require_matching_version
from app.core.errors import DomainError
from app.modules.admin_config.service import runtime
from app.modules.people_access.model import Officer, Role, User
from app.modules.people_access.services import people
from app.modules.people_access.services.identity_collections import IdentityApplicationService
from app.shared.pagination import parse_limit


class PeopleCollectionService:
    def __init__(self, resource: str) -> None:
        self.resource = resource
        self.identity = IdentityApplicationService(self)

    def kind(self) -> str:
        try:
            return {"officers": "officer", "roles": "role", "users": "user"}[self.resource]
        except KeyError as exc:
            raise HTTPException(404, "People resource not found") from exc

    async def actor_officer_id(self, db, user):
        return (await people.ensure_officer_for_user(db, user)).id

    def _assert_version(self, current, expected) -> None:
        if self.kind() == "user":
            require_matching_version(current, expected)

    async def _assert_writable(self, db) -> None:
        general = runtime.general_defaults(await runtime.load_app_config(db))
        if general["maintenanceMode"]:
            raise DomainError("MAINTENANCE", "System is in maintenance mode", 503)
        if general["readOnlyMode"]:
            raise DomainError("READ_ONLY", "System is in read-only mode", 403)

    async def _get_model(self, db, kind: str, entity_id: str):
        try:
            row = await db.get({"officer": Officer, "role": Role, "user": User}[kind], uuid.UUID(entity_id))
        except ValueError as exc:
            raise HTTPException(404, "Not found") from exc
        if not row:
            raise HTTPException(404, "Not found")
        return row

    async def list_items(self, db, user, params) -> dict:
        page = max(1, int(params.get("page") or 1))
        defaults = runtime.general_defaults(await runtime.load_app_config(db))
        limit = parse_limit(params.get("limit"), default=defaults["defaultPageSize"])
        return await self.identity.list_items(
            db, user, params, page, limit,
            params.get("q") or params.get("search"), params.get("status"),
        )

    async def get_item(self, db, entity_id: str, user=None) -> dict:
        return await self.identity.get_item(db, entity_id)

    async def create(self, db, user, payload: dict, raw_payload=None) -> dict:
        await self._assert_writable(db)
        return await self.identity.create(db, user, payload)

    async def update(self, db, user, entity_id: str, body: dict) -> dict:
        await self._assert_writable(db)
        current = await self.get_item(db, entity_id, user)
        expected = body.pop("version", None)
        self._assert_version(current.get("version"), expected)
        return await self.identity.update(db, user, entity_id, body, current)

    async def soft_delete(self, db, user, entity_id: str, body=None) -> dict:
        await self._assert_writable(db)
        expected = (body or {}).get("version")
        if self.kind() == "officer":
            return await self.identity.purge(db, user, entity_id, expected)
        return await self.identity.soft_delete(db, entity_id, expected)

    async def purge(self, db, user, entity_id: str, body=None) -> dict:
        await self._assert_writable(db)
        return await self.identity.purge(db, user, entity_id, (body or {}).get("version"))

    async def lifecycle(self, db, user, entity_id: str, status: str, body=None) -> dict:
        payload = {"status": status}
        if (body or {}).get("version") is not None:
            payload["version"] = body["version"]
        return await self.update(db, user, entity_id, payload)

    async def set_stage(self, db, user, entity_id, stage, body=None):
        raise HTTPException(404, "Not found")


__all__ = ["PeopleCollectionService"]
