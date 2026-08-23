"""Typed people/access collections — users, roles, officers on relational tables."""

from __future__ import annotations

import math
import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.datetime import utcnow
from app.core.errors import DomainError
from app.core.security import hash_password, revoke_user_tokens
from app.models.access import Role
from app.models.people import Officer, User
from app.modules.people_access.services.identity import normalize_identity_payload, parse_role_level
import app.modules.people_access.services.people as people


class IdentityApplicationService:
    def __init__(self, host):
        self.host = host

    def kind(self) -> str:
        return self.host.kind()

    async def list_items(self, db: AsyncSession, user: User, params: dict, page: int, limit: int, q, status) -> dict:
        kind = self.kind()
        if kind == "officer":
            filters = []
            if not status or status in {"all", "all-status"}:
                filters.append(Officer.is_active == 1)
            if q:
                filters.append(Officer.nam.ilike(f"%{q}%"))
            stmt = select(Officer)
            if filters:
                stmt = stmt.where(*filters)
            total = await db.scalar(select(func.count()).select_from(Officer).where(*filters)) if filters else await db.scalar(select(func.count()).select_from(Officer))
            rows = (await db.scalars(stmt.order_by(Officer.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
            return {"data": [people.officer_to_payload(row) for row in rows], "meta": {"page": page, "limit": limit, "total": total or 0, "totalPages": max(1, math.ceil((total or 0) / limit))}}

        if kind == "role":
            rows = (await db.scalars(select(Role).order_by(Role.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
            data = []
            for row in rows:
                perms = await people.permissions_for_role_id(db, row.id)
                data.append(people.role_to_payload(row, perms))
            return {"data": data, "meta": {"page": page, "limit": limit, "total": len(data), "totalPages": 1}}

        rows = (await db.scalars(select(User).order_by(User.updated_at.desc()).offset((page - 1) * limit).limit(limit))).all()
        return {"data": await people.hydrate_user_payloads(db, rows), "meta": {"page": page, "limit": limit, "total": len(rows), "totalPages": 1}}

    async def get_item(self, db: AsyncSession, entity_id: str) -> dict:
        uid = uuid.UUID(entity_id)
        kind = self.kind()
        if kind == "officer":
            row = await db.get(Officer, uid)
            if not row:
                raise HTTPException(404, "Not found")
            return people.officer_to_payload(row)
        if kind == "role":
            row = await db.get(Role, uid)
            if not row:
                raise HTTPException(404, "Not found")
            return people.role_to_payload(row, await people.permissions_for_role_id(db, row.id))
        row = await db.get(User, uid)
        if not row:
            raise HTTPException(404, "Not found")
        return await people.user_payload(db, row)

    async def create(self, db: AsyncSession, user: User, payload: dict) -> dict:
        officer_id = await self.host.actor_officer_id(db, user)
        kind = self.kind()
        if kind == "officer":
            row = Officer(
                nam=str(payload.get("name") or ""),
                email=payload.get("email"),
                organization_id=uuid.UUID(str(payload["organizationId"])) if payload.get("organizationId") or payload.get("departmentId") else None,
                role_id=uuid.UUID(str(payload["roleId"])) if payload.get("roleId") else None,
                is_active=0 if payload.get("status") == "inactive" else 1,
                profile_url=payload.get("profileUrl") or payload.get("avatar"),
                created_by=officer_id,
                updated_by=officer_id,
            )
            if payload.get("departmentId") and not row.organization_id:
                row.organization_id = uuid.UUID(str(payload["departmentId"]))
            db.add(row)
            await db.commit()
            await db.refresh(row)
            return people.officer_to_payload(row)

        if kind == "role":
            data = await normalize_identity_payload(db, "roles", payload, actor=user)
            row = Role(
                nam=str(data.get("name") or data.get("code") or "Role"),
                description=data.get("description"),
                lvl=parse_role_level(data.get("lvl")),
                is_active=0 if data.get("status") == "inactive" else 1,
                created_by=officer_id,
                updated_by=officer_id,
            )
            db.add(row)
            await db.flush()
            await people.replace_role_permissions(db, row.id, list(data.get("permissions") or []))
            await db.commit()
            await db.refresh(row)
            return people.role_to_payload(row, await people.permissions_for_role_id(db, row.id))

        data = await normalize_identity_payload(db, "users", payload, actor=user)
        linked_officer_id = uuid.UUID(str(data["officerId"])) if data.get("officerId") else None
        row = User(
            email=data["email"],
            name=data["name"],
            password_hash=hash_password(str(data["password"])),
            role=str(data.get("roleName") or "User"),
            role_id=uuid.UUID(str(data["roleId"])),
            permissions=list(data.get("_permissions") or []),
            active=data.get("status", "active") != "inactive",
            status=str(data.get("status") or "active"),
            officer_id=linked_officer_id,
            created_by=officer_id,
            updated_by=officer_id,
        )
        db.add(row)
        await db.flush()
        if linked_officer_id:
            await people.bind_user_officer(db, row, linked_officer_id)
        else:
            await people.ensure_officer_for_user(db, row, row.role_id)
        await db.commit()
        await db.refresh(row)
        return await people.user_payload(db, row)

    async def update(self, db: AsyncSession, user: User, entity_id: str, body: dict, current: dict) -> dict:
        officer_id = await self.host.actor_officer_id(db, user)
        kind = self.kind()
        uid = uuid.UUID(entity_id)
        if kind == "role":
            row = await db.get(Role, uid)
            if not row:
                raise HTTPException(404, "Not found")
            data = await normalize_identity_payload(db, "roles", {**current, **body}, row.id, actor=user)
            row.nam = str(data.get("name") or row.nam)
            row.description = data.get("description")
            if "status" in body:
                row.is_active = 0 if body["status"] == "inactive" else 1
            row.updated_by = officer_id
            await people.replace_role_permissions(db, row.id, list(data.get("permissions") or []))
            users = (await db.scalars(select(User).where(User.role_id == row.id))).all()
            perms = await people.permissions_for_role_id(db, row.id)
            for account in users:
                account.permissions = perms
                account.role = row.nam
                await revoke_user_tokens(str(account.id))
            await db.commit()
            return people.role_to_payload(row, perms)

        if kind == "user":
            row = await db.get(User, uid)
            if not row:
                raise HTTPException(404, "Not found")
            data = await normalize_identity_payload(db, "users", {**current, **body}, row.id, actor=user)
            row.name = data["name"]
            row.email = data["email"]
            if data.get("roleId"):
                row.role_id = uuid.UUID(str(data["roleId"]))
                row.role = str(data.get("roleName") or row.role)
                if data.get("_permissions") is not None:
                    row.permissions = list(data["_permissions"])
            if data.get("password"):
                row.password_hash = hash_password(str(data["password"]))
            if body.get("officerId"):
                await people.bind_user_officer(db, row, uuid.UUID(str(body["officerId"])))
            else:
                await people.ensure_officer_for_user(db, row, row.role_id)
            if "status" in body:
                row.status = str(body["status"])
                row.active = body["status"] != "inactive"
            row.updated_by = officer_id
            row.version += 1
            await db.commit()
            return await people.user_payload(db, row)

        row = await db.get(Officer, uid)
        if not row:
            raise HTTPException(404, "Not found")
        if "name" in body:
            row.nam = str(body["name"])
        if "email" in body:
            row.email = body["email"]
        if "organizationId" in body or "departmentId" in body:
            raw = body.get("organizationId") or body.get("departmentId")
            row.organization_id = uuid.UUID(str(raw)) if raw else None
        if "status" in body:
            row.is_active = 0 if body["status"] == "inactive" else 1
        row.updated_by = officer_id
        await db.commit()
        return people.officer_to_payload(row)

    async def soft_delete(self, db: AsyncSession, entity_id: str, expected) -> dict:
        uid = uuid.UUID(entity_id)
        kind = self.kind()
        if kind == "role":
            row = await db.get(Role, uid)
            if not row:
                raise HTTPException(404, "Not found")
            row.is_active = 0
            await db.commit()
            return {"id": entity_id}
        if kind == "user":
            row = await db.get(User, uid)
            if not row:
                raise HTTPException(404, "Not found")
            self.host._assert_version(row.version, expected)
            row.active = False
            row.status = "deleted"
            row.version += 1
            await db.commit()
            return {"id": entity_id}
        raise HTTPException(404, "Not found")

    async def purge(self, db: AsyncSession, user: User, entity_id: str, expected) -> dict:
        uid = uuid.UUID(entity_id)
        kind = self.kind()
        if kind == "user" and uid == user.id:
            raise DomainError("CONFLICT", "You cannot purge your own account", 409)
        if kind == "role":
            assigned = await db.scalar(select(func.count()).select_from(User).where(User.role_id == uid))
            if assigned:
                raise DomainError("CONFLICT", f"Role is assigned to {assigned} users", 409)
        model = {"role": Role, "user": User, "officer": Officer}[kind]
        row = await db.get(model, uid)
        if not row:
            raise HTTPException(404, "Not found")
        if kind == "user":
            self.host._assert_version(row.version, expected)
            officer = await db.scalar(select(Officer).where(Officer.auth_id == uid))
            if officer:
                await db.delete(officer)
        await db.delete(row)
        await db.commit()
        return {"id": entity_id}
