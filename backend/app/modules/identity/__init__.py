import secrets
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.permissions import ALL_PERMISSIONS, expand_permission_rows, normalize_permission_payload
from app.core.security import hash_password, revoke_user_tokens
from app.core.config import settings
from app.db import Entity, User

SECRET_KEYS = {"password", "passwordConfirmation", "passwordHash", "currentPassword", "token", "secret", "secretKey", "accessKey", "clientSecret", "botToken"}


def strip_secrets(payload: dict) -> dict:
    return {key: value for key, value in payload.items() if key not in SECRET_KEYS}


async def normalize_identity_payload(db: AsyncSession, resource: str, payload: dict, current_id: uuid.UUID | None = None) -> dict:
    data = dict(payload)
    excluded = current_id or uuid.UUID(int=0)
    if resource == "roles":
        try:
            data = normalize_permission_payload(data)
        except (ValueError, TypeError) as exc:
            raise HTTPException(422, str(exc)) from exc
        data["code"] = str(data.get("code") or "").strip().upper()
        data["name"] = str(data.get("name") or "").strip()
        if not data["code"] or not data["name"]:
            raise HTTPException(422, "Role code and name are required")
        duplicate = await db.scalar(select(Entity).where(Entity.resource == "roles", Entity.payload["code"].as_string() == data["code"], Entity.id != excluded))
        if duplicate:
            raise HTTPException(409, "Role code already exists")
    if resource == "users":
        data["email"] = str(data.get("email") or "").strip().lower()
        data["name"] = str(data.get("name") or "").strip()
        if not data["name"] or "@" not in data["email"]:
            raise HTTPException(422, "A valid email and name are required")
        if data.get("password") and len(str(data["password"])) < settings.minimum_password_length:
            raise HTTPException(422, f"Password must contain at least {settings.minimum_password_length} characters")
        duplicate = await db.scalar(select(User).where(User.email == data["email"], User.id != excluded))
        if duplicate:
            raise HTTPException(409, "User email already exists")
        role_id = data.get("roleId")
        if role_id:
            try:
                role = await db.scalar(select(Entity).where(Entity.resource == "roles", Entity.id == uuid.UUID(str(role_id)), Entity.status == "active"))
            except ValueError:
                role = None
            if not role:
                raise HTTPException(422, "Assigned role does not exist or is inactive")
            data["roleName"] = (role.payload or {}).get("name") or "User"
        officer_id = data.get("officerId")
        if officer_id:
            try:
                officer = await db.scalar(select(Entity).where(Entity.resource == "officers", Entity.id == uuid.UUID(str(officer_id)), Entity.status == "active"))
            except ValueError:
                officer = None
            if not officer:
                raise HTTPException(422, "Linked officer does not exist or is inactive")
            assigned = await db.scalar(select(User).where(User.officer_id == uuid.UUID(str(officer_id)), User.id != excluded))
            if assigned:
                raise HTTPException(409, "Officer is already linked to another user")
    return data


async def permissions_for_role(db: AsyncSession, payload: dict) -> list[str]:
    rows = payload.get("permissionRows")
    if rows:
        return expand_permission_rows(rows)
    if payload.get("permissions"):
        return list(payload["permissions"])
    role_id = payload.get("roleId")
    if not role_id:
        return []
    try:
        row = await db.scalar(select(Entity).where(Entity.resource == "roles", Entity.id == uuid.UUID(str(role_id))))
    except Exception:
        row = None
    if not row:
        return []
    return await permissions_for_role(db, row.payload or {})


async def sync_login_user(db: AsyncSession, entity: Entity, payload: dict) -> User | None:
    email = str(payload.get("email") or "").strip().lower()
    name = str(payload.get("name") or email or "User")
    if not email:
        return None
    permissions = await permissions_for_role(db, payload)
    account = await db.get(User, entity.id)
    if account is None:
        account = await db.scalar(select(User).where(User.email == email))
    active = entity.status == "active"
    if account is None:
        password = str(payload.get("password") or secrets.token_urlsafe(18))
        role_id = None
        if payload.get("roleId"):
            try:
                role_id = uuid.UUID(str(payload["roleId"]))
            except ValueError:
                role_id = None
        account = User(
            id=entity.id,
            email=email,
            name=name,
            password_hash=hash_password(password),
            role=str(payload.get("roleName") or "User"),
            permissions=permissions or [],
            active=active,
            role_id=role_id,
        )
        db.add(account)
    old_permissions = set(account.permissions or [])
    account.name = name
    account.email = email
    account.role = str(payload.get("roleName") or account.role)
    if payload.get("roleId"):
        try:
            account.role_id = uuid.UUID(str(payload["roleId"]))
        except ValueError:
            pass
    if permissions:
        account.permissions = permissions
    if payload.get("password"):
        account.password_hash = hash_password(str(payload["password"]))
    account.active = active
    account.status = entity.status
    account.version = entity.version
    account.updated_at = datetime.now(timezone.utc)
    if payload.get("officerId"):
        account.officer_id = uuid.UUID(str(payload["officerId"]))
    elif "officerId" in payload:
        account.officer_id = None
    if not active or old_permissions != set(account.permissions or []):
        await revoke_user_tokens(str(account.id))
    return account


async def refresh_role_users(db: AsyncSession, role: Entity) -> None:
    users = (await db.scalars(select(Entity).where(Entity.resource == "users"))).all()
    keys = await permissions_for_role(db, role.payload or {})
    for row in users:
        if str((row.payload or {}).get("roleId") or "") != str(role.id):
            continue
        account = await db.get(User, row.id)
        if account:
            account.permissions = keys
            account.role = str((role.payload or {}).get("name") or account.role)
            row.payload = {**(row.payload or {}), "roleName": account.role}
            await revoke_user_tokens(str(account.id))


async def ensure_admin_entity(db: AsyncSession, user: User) -> None:
    existing = await db.scalar(select(Entity).where(Entity.resource == "users", Entity.id == user.id))
    payload = {
        "name": user.name,
        "email": user.email,
        "roleName": user.role,
        "status": "active",
        "permissions": user.permissions or ALL_PERMISSIONS,
    }
    if existing:
        existing.payload = {**(existing.payload or {}), **payload}
        return
    db.add(Entity(id=user.id, resource="users", payload=payload, status="active", created_by=user.id, updated_by=user.id))
