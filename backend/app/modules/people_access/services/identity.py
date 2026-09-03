import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import DomainError
from app.core.permissions import normalize_permission_payload
from app.core.privileged import is_unrestricted, is_unrestricted_role_name
from app.core.redaction import strip_secrets
from app.modules.people_access.model import User
from app.modules.people_access.model import Officer, Role
import app.modules.people_access.services.people as people

USER_AUTHORITY_KEYS = ("permissions", "permissionRows", "roleName", "role")


def parse_role_level(value, default: int = 1) -> int:
    if value is None or value == "":
        return default
    return int(value)


def strip_user_authority(payload: dict) -> dict:
    """Drop client-supplied role names and permission arrays. Server loads those from Role.id."""
    return {key: value for key, value in payload.items() if key not in USER_AUTHORITY_KEYS}


def validate_user_password(password, *, required: bool) -> None:
    value = "" if password is None else str(password)
    if required and not value:
        raise DomainError("VALIDATION_ERROR", "Password is required", 422)
    if value and len(value) < settings.minimum_password_length:
        raise DomainError(
            "VALIDATION_ERROR",
            f"Password must contain at least {settings.minimum_password_length} characters",
            422,
        )


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
        duplicate = await db.scalar(
            select(Role.id).where(
                Role.id != excluded,
                or_(
                    func.lower(Role.nam) == data["name"].lower(),
                    func.upper(func.replace(Role.nam, " ", "_")) == data["code"],
                ),
            )
        )
        if duplicate:
            raise DomainError("CONFLICT", "Role code already exists", 409)
    if resource == "users":
        data["email"] = str(data.get("email") or "").strip().lower()
        data["name"] = str(data.get("name") or "").strip()
        if not data["name"] or "@" not in data["email"]:
            raise DomainError("VALIDATION_ERROR", "A valid email and name are required", 422)
        validate_user_password(data.get("password"), required=current_id is None)
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
        officer_id = data.get("officerId") or None
        data["officerId"] = str(officer_id) if officer_id else None
        if officer_id:
            try:
                officer = await db.get(Officer, uuid.UUID(str(officer_id)))
            except ValueError:
                officer = None
            if not officer or not officer.is_active:
                raise DomainError("VALIDATION_ERROR", "Linked officer does not exist or is inactive", 422)
            assigned = await db.scalar(
                select(User).where(User.officer_id == uuid.UUID(str(officer_id)), User.id != excluded)
            )
            if assigned:
                raise DomainError("CONFLICT", "Officer is already linked to another user", 409)
            if officer.auth_id is not None and officer.auth_id != excluded:
                raise DomainError("CONFLICT", "Officer is already linked to another user", 409)
    return data


async def ensure_admin_entity(db: AsyncSession, user: User) -> None:
    """Keep the bootstrap admin on the relational User row. Entity user bags are no longer written."""
    user.active = True
    if user.status in {None, "", "deleted"}:
        user.status = "active"
    if not user.role:
        user.role = "SuperAdmin"
