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
from app.modules.people_access.model import Officer, Role, User
from app.modules.people_access.services.identity import normalize_identity_payload, parse_role_level
import app.modules.people_access.services.people as people


async def _resolve_officer_role_id(db: AsyncSession, payload: dict) -> uuid.UUID | None:
    """Officers store a role FK. A typed role name (case-insensitive) is resolved here."""
    name = str(payload.get("roleName") or "").strip()
    if name:
        role = await db.scalar(select(Role).where(func.lower(Role.nam) == name.lower()))
        if not role:
            message = "Role not found"
            raise DomainError("VALIDATION_ERROR", message, 422, fields=[{"field": "roleName", "message": message}])
        return role.id
    raw = payload.get("roleId")
    if not raw:
        return None
    try:
        return uuid.UUID(str(raw))
    except (TypeError, ValueError):
        return None


def _field_error(field: str, message: str) -> list[dict]:
    return [{"field": field, "message": message}]


async def _create_officer_login(
    db: AsyncSession,
    officer: Officer,
    payload: dict,
    role_id: uuid.UUID | None,
    actor: User,
    actor_officer_id: uuid.UUID | None,
) -> None:
    """Provision a login account for an officer (role is required for a user row)."""
    if not role_id:
        message = "A role is required to enable login"
        raise DomainError("VALIDATION_ERROR", message, 422, fields=_field_error("roleName", message))
    data = await normalize_identity_payload(
        db,
        "users",
        {
            "email": payload.get("email"),
            "name": officer.nam,
            "password": payload.get("password"),
            "roleId": str(role_id),
        },
        actor=actor,
    )
    user = User(
        email=data["email"],
        name=data["name"],
        password_hash=hash_password(str(data["password"])),
        role=str(data.get("roleName") or "User"),
        role_id=uuid.UUID(str(data["roleId"])),
        permissions=list(data.get("_permissions") or []),
        active=True,
        status="active",
        officer_id=officer.id,
        created_by=actor_officer_id,
        updated_by=actor_officer_id,
    )
    db.add(user)
    await db.flush()
    officer.auth_id = user.id
    if not officer.email:
        officer.email = user.email


async def _update_officer_login(
    db: AsyncSession,
    officer: Officer,
    payload: dict,
    role_id: uuid.UUID | None,
    actor: User,
    actor_officer_id: uuid.UUID | None,
) -> None:
    user = await db.get(User, officer.auth_id) if officer.auth_id else None
    if user is None:
        await _create_officer_login(db, officer, payload, role_id, actor, actor_officer_id)
        return
    data = await normalize_identity_payload(
        db,
        "users",
        {
            "email": payload.get("email") or user.email,
            "name": officer.nam,
            "password": payload.get("password"),
            "roleId": str(role_id or user.role_id),
        },
        user.id,
        actor=actor,
    )
    user.name = data["name"]
    user.email = data["email"]
    if role_id:
        user.role_id = uuid.UUID(str(data["roleId"]))
        user.role = str(data.get("roleName") or user.role)
        if data.get("_permissions") is not None:
            user.permissions = list(data["_permissions"])
    if data.get("password"):
        user.password_hash = hash_password(str(data["password"]))
    user.officer_id = officer.id
    user.updated_by = actor_officer_id
    user.version += 1
    if not officer.email:
        officer.email = user.email


async def _disable_officer_login(db: AsyncSession, officer: Officer) -> None:
    """Turn an officer back into a mention-only record without deleting history."""
    if not officer.auth_id:
        return
    user = await db.get(User, officer.auth_id)
    if user is not None:
        user.active = False
        user.status = "disabled"
        user.version += 1
    officer.auth_id = None


async def _apply_officer_authentication(
    db: AsyncSession,
    officer: Officer,
    payload: dict,
    role_id: uuid.UUID | None,
    actor: User,
    actor_officer_id: uuid.UUID | None,
) -> None:
    enabled = payload.get("authenticationEnabled")
    if enabled is None:
        return
    if enabled:
        await _update_officer_login(db, officer, payload, role_id, actor, actor_officer_id)
    else:
        await _disable_officer_login(db, officer)


class IdentityApplicationService:
    def __init__(self, host):
        self.host = host

    def kind(self) -> str:
        return self.host.kind()

    async def list_items(self, db: AsyncSession, user: User, params: dict, page: int, limit: int, q, status) -> dict:
        from app.shared.list_query import date_filters, order_clause

        kind = self.kind()
        if kind == "officer":
            filters = []
            if not status or status in {"all", "all-status"}:
                filters.append(Officer.is_active == 1)
            elif "inactive" in (status or ""):
                filters.append(Officer.is_active == 0)
            if q:
                filters.append(Officer.nam.ilike(f"%{q}%"))
            filters.extend(date_filters(params, Officer.updated_at))
            stmt = select(Officer)
            if filters:
                stmt = stmt.where(*filters)
            count_stmt = select(func.count()).select_from(Officer)
            total = (await db.scalar(count_stmt.where(*filters)) if filters else await db.scalar(count_stmt)) or 0
            stmt = stmt.order_by(order_clause(params, Officer)).offset((page - 1) * limit).limit(limit)
            rows = (await db.scalars(stmt)).all()
            return {
                "data": await people.hydrate_officer_payloads(db, rows),
                "meta": {"page": page, "limit": limit, "total": total or 0, "totalPages": max(1, math.ceil((total or 0) / limit))},
            }

        if kind == "role":
            filters = []
            if status and status not in {"all", "all-status"}:
                if "inactive" in (status or ""):
                    filters.append(Role.is_active == 0)
                else:
                    filters.append(Role.is_active == 1)
            if q:
                filters.append(Role.nam.ilike(f"%{q}%"))
            filters.extend(date_filters(params, Role.updated_at))
            count_stmt = select(func.count()).select_from(Role)
            total = (await db.scalar(count_stmt.where(*filters)) if filters else await db.scalar(count_stmt)) or 0
            stmt = select(Role).order_by(order_clause(params, Role)).offset((page - 1) * limit).limit(limit)
            if filters:
                stmt = stmt.where(*filters)
            rows = (await db.scalars(stmt)).all()
            data = []
            for row in rows:
                perms = await people.permissions_for_role_id(db, row.id)
                data.append(people.role_to_payload(row, perms, await people.creator_scoped_codes_for_role(db, row.id)))
            return {"data": data, "meta": {"page": page, "limit": limit, "total": total or 0, "totalPages": max(1, math.ceil((total or 0) / limit))}}

        filters = []
        if q:
            from sqlalchemy import or_ as _or

            filters.append(_or(User.email.ilike(f"%{q}%"), User.name.ilike(f"%{q}%")))
        if status and status not in {"all", "all-status"}:
            if "inactive" in (status or ""):
                filters.append(User.active.is_(False))
            else:
                filters.append(User.active.is_(True))
        filters.extend(date_filters(params, User.updated_at))
        count_stmt = select(func.count()).select_from(User)
        total = (await db.scalar(count_stmt.where(*filters)) if filters else await db.scalar(count_stmt)) or 0
        stmt = select(User).order_by(order_clause(params, User)).offset((page - 1) * limit).limit(limit)
        if filters:
            stmt = stmt.where(*filters)
        rows = (await db.scalars(stmt)).all()
        return {"data": await people.hydrate_user_payloads(db, rows), "meta": {"page": page, "limit": limit, "total": total or 0, "totalPages": max(1, math.ceil((total or 0) / limit))}}

    async def get_item(self, db: AsyncSession, entity_id: str) -> dict:
        uid = uuid.UUID(entity_id)
        kind = self.kind()
        if kind == "officer":
            row = await db.get(Officer, uid)
            if not row:
                raise HTTPException(404, "Not found")
            hydrated = await people.hydrate_officer_payloads(db, [row])
            return hydrated[0]
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
            role_id = await _resolve_officer_role_id(db, payload)
            row = Officer(
                nam=str(payload.get("name") or ""),
                email=payload.get("email"),
                organization_id=uuid.UUID(str(payload["organizationId"])) if payload.get("organizationId") or payload.get("departmentId") else None,
                role_id=role_id,
                is_active=0 if payload.get("status") == "inactive" else 1,
                profile_url=payload.get("profileUrl") or payload.get("avatar"),
                created_by=officer_id,
                updated_by=officer_id,
            )
            if payload.get("departmentId") and not row.organization_id:
                row.organization_id = uuid.UUID(str(payload["departmentId"]))
            db.add(row)
            await db.flush()
            await _apply_officer_authentication(db, row, payload, role_id, user, officer_id)
            await db.flush()
            await db.refresh(row)
            return (await people.hydrate_officer_payloads(db, [row]))[0]

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
            creator_scoped = people.creator_scoped_codes_from_rows(data.get("permissionRows"))
            await people.replace_role_permissions(db, row.id, list(data.get("permissions") or []), creator_scoped)
            await db.flush()
            await db.refresh(row)
            return people.role_to_payload(row, await people.permissions_for_role_id(db, row.id), await people.creator_scoped_codes_for_role(db, row.id))

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
        await db.flush()
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
            previous_perms = set(await people.permissions_for_role_id(db, row.id))
            data = await normalize_identity_payload(db, "roles", {**current, **body}, row.id, actor=user)
            name_changed = str(data.get("name") or row.nam) != row.nam
            row.nam = str(data.get("name") or row.nam)
            row.description = data.get("description")
            if "status" in body:
                row.is_active = 0 if body["status"] == "inactive" else 1
            row.updated_by = officer_id
            creator_scoped = people.creator_scoped_codes_from_rows(data.get("permissionRows"))
            await people.replace_role_permissions(db, row.id, list(data.get("permissions") or []), creator_scoped)
            perms = await people.permissions_for_role_id(db, row.id)
            permissions_changed = set(perms) != previous_perms
            # Status-only (or name-only) edits must not log users out. Only a
            # real permission change invalidates sessions so the denormalized
            # users.permissions snapshot stays authoritative. The acting admin is
            # exempt: their snapshot is updated above and re-read from the DB on
            # every request, and revoking it would only break the in-flight save
            # (CSRF/session binding fails on the follow-up attachment request).
            if permissions_changed or name_changed:
                users = (await db.scalars(select(User).where(User.role_id == row.id))).all()
                for account in users:
                    account.permissions = perms
                    account.role = row.nam
                    if permissions_changed and str(account.id) != str(user.id):
                        await revoke_user_tokens(str(account.id))
            await db.flush()
            return people.role_to_payload(row, perms, await people.creator_scoped_codes_for_role(db, row.id))

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
            await db.flush()
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
        if "roleName" in body or "roleId" in body:
            row.role_id = await _resolve_officer_role_id(db, body)
        if "status" in body or "isActive" in body:
            if "isActive" in body:
                row.is_active = 1 if body.get("isActive") else 0
            else:
                row.is_active = 0 if body["status"] == "inactive" else 1
        if "authenticationEnabled" in body:
            await _apply_officer_authentication(db, row, body, row.role_id, user, officer_id)
        row.updated_by = officer_id
        await db.flush()
        return (await people.hydrate_officer_payloads(db, [row]))[0]

    async def soft_delete(self, db: AsyncSession, entity_id: str, expected) -> dict:
        uid = uuid.UUID(entity_id)
        kind = self.kind()
        if kind == "role":
            row = await db.get(Role, uid)
            if not row:
                raise HTTPException(404, "Not found")
            row.is_active = 0
            await db.flush()
            return {"id": entity_id}
        if kind == "user":
            row = await db.get(User, uid)
            if not row:
                raise HTTPException(404, "Not found")
            self.host._assert_version(row.version, expected)
            row.active = False
            row.status = "deleted"
            row.version += 1
            await db.flush()
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
        if kind == "officer":
            # Keep the account row for history, but revoke its ability to sign in.
            await _disable_officer_login(db, row)
        await db.delete(row)
        await db.flush()
        return {"id": entity_id}
