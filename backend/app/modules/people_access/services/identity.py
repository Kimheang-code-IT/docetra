import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import DomainError
from app.core.permissions import expand_permission_rows, normalize_permission_payload
from app.core.privileged import is_unrestricted, is_unrestricted_role_name


def parse_role_level(value, default: int = 1) -> int:
    if value is None or value == "":
        return default
    return int(value)
from app.core.security import hash_password, revoke_user_tokens
from app.db import Entity, User
from app.models.access import Role
import app.modules.people_access.services.people as people

SECRET_KEYS = {"password", "passwordConfirmation", "passwordHash", "currentPassword", "token", "secret", "secretKey", "accessKey", "clientSecret", "botToken"}
USER_AUTHORITY_KEYS = ("permissions", "permissionRows", "roleName", "role")


def strip_secrets(payload: dict) -> dict:
    return {key: value for key, value in payload.items() if key not in SECRET_KEYS}


def strip_user_authority(payload: dict) -> dict:
    """Drop client-supplied role names and permission arrays. Server loads those from Role.id."""
    return {key: value for key, value in payload.items() if key not in USER_AUTHORITY_KEYS}


async def load_assignable_role(db: AsyncSession, role_id, actor: User | None) -> Role:
    try:
        uid = uuid.UUID(str(role_id))
    except (TypeError, ValueError) as exc:
        raise DomainError("VALIDATION_ERROR", "Assigned role does not exist or is inactive", 422) from exc
    role = await db.get(Role, uid)
    if not role or not role.is_active:
        raise DomainError("VALIDATION_ERROR", "Assigned role does not exist or is inactive", 422)
    if actor is not None and not is_unrestricted(actor):
        if is_unrestricted_role_name(role.nam) or parse_role_level(role.lvl) == 0:
            raise DomainError("FORBIDDEN", "You cannot assign a privileged role", 403)
    return role


async def normalize_identity_payload(
    db: AsyncSession,
    resource: str,
    payload: dict,
    current_id: uuid.UUID | None = None,
    *,
    actor: User | None = None,
) -> dict:
    data = dict(payload)
    excluded = current_id or uuid.UUID(int=0)
    if resource == "roles":
        try:
            data = normalize_permission_payload(data)
        except (ValueError, TypeError) as exc:
            raise DomainError("VALIDATION_ERROR", str(exc), 422) from exc
        data["code"] = str(data.get("code") or "").strip().upper()
        data["name"] = str(data.get("name") or "").strip()
        if not data["code"] or not data["name"]:
            raise DomainError("VALIDATION_ERROR", "Role code and name are required", 422)
        if actor is not None and not is_unrestricted(actor):
            if is_unrestricted_role_name(data["name"]) or parse_role_level(data.get("lvl")) == 0:
                raise DomainError("FORBIDDEN", "You cannot create or modify a privileged role", 403)
        if current_id:
            existing_role = await db.get(Role, current_id)
            if existing_role and (is_unrestricted_role_name(existing_role.nam) or parse_role_level(existing_role.lvl) == 0):
                if actor is None or not is_unrestricted(actor):
                    raise DomainError("FORBIDDEN", "You cannot modify a privileged role", 403)
        duplicate = await db.scalar(select(Entity).where(Entity.resource == "roles", Entity.payload["code"].as_string() == data["code"], Entity.id != excluded))
        if duplicate:
            raise DomainError("CONFLICT", "Role code already exists", 409)
    if resource == "users":
        data["email"] = str(data.get("email") or "").strip().lower()
        data["name"] = str(data.get("name") or "").strip()
        if not data["name"] or "@" not in data["email"]:
            raise DomainError("VALIDATION_ERROR", "A valid email and name are required", 422)
        if data.get("password") and len(str(data["password"])) < settings.minimum_password_length:
            raise DomainError("VALIDATION_ERROR", f"Password must contain at least {settings.minimum_password_length} characters", 422)
        duplicate = await db.scalar(select(User).where(User.email == data["email"], User.id != excluded))
        if duplicate:
            raise DomainError("CONFLICT", "User email already exists", 409)
        data = strip_user_authority(data)
        role_id = data.get("roleId")
        if not role_id:
            if current_id is None:
                raise DomainError("VALIDATION_ERROR", "A valid roleId is required", 422)
        else:
            role = await load_assignable_role(db, role_id, actor)
            data["roleId"] = str(role.id)
            data["roleName"] = role.nam
            data["_permissions"] = await people.permissions_for_role_id(db, role.id)
        officer_id = data.get("officerId")
        if officer_id:
            try:
                officer = await db.scalar(select(Entity).where(Entity.resource == "officers", Entity.id == uuid.UUID(str(officer_id)), Entity.status == "active"))
            except ValueError:
                officer = None
            if not officer:
                raise DomainError("VALIDATION_ERROR", "Linked officer does not exist or is inactive", 422)
            assigned = await db.scalar(select(User).where(User.officer_id == uuid.UUID(str(officer_id)), User.id != excluded))
            if assigned:
                raise DomainError("CONFLICT", "Officer is already linked to another user", 409)
    return data


async def permissions_for_role(db: AsyncSession, payload: dict) -> list[str]:
    role_id = payload.get("roleId")
    if role_id:
        try:
            return await people.permissions_for_role_id(db, uuid.UUID(str(role_id)))
        except (TypeError, ValueError):
            return []
    rows = payload.get("permissionRows")
    if rows:
        return expand_permission_rows(rows)
    return []


async def sync_login_user(db: AsyncSession, entity: Entity, payload: dict) -> User | None:
    email = str(payload.get("email") or "").strip().lower()
    name = str(payload.get("name") or email or "User")
    if not email:
        return None
    role_id = None
    if payload.get("roleId"):
        try:
            role_id = uuid.UUID(str(payload["roleId"]))
        except ValueError:
            role_id = None
    role_name = "User"
    permissions: list[str] = []
    if role_id:
        role = await db.get(Role, role_id)
        if role:
            role_name = role.nam
            permissions = await people.permissions_for_role_id(db, role.id)
    account = await db.get(User, entity.id)
    if account is None:
        account = await db.scalar(select(User).where(User.email == email))
    active = entity.status == "active"
    if account is None:
        password = str(payload.get("password") or secrets.token_urlsafe(18))
        account = User(
            id=entity.id,
            email=email,
            name=name,
            password_hash=hash_password(password),
            role=role_name,
            permissions=permissions,
            active=active,
            role_id=role_id,
        )
        db.add(account)
    old_permissions = set(account.permissions or [])
    account.name = name
    account.email = email
    if role_id:
        account.role_id = role_id
        account.role = role_name
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
    from app.core.permissions import ALL_PERMISSIONS

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
