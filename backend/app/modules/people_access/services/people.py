"""People/access helpers: menu seed, role permissions, officer linkage."""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.core.permissions import ALL_PERMISSIONS, DOCUMENT_TYPES, PREFIXES
from app.models.access import Menu, Permission, Role
from app.models.people import Officer, User


async def seed_menus(db: AsyncSession) -> None:
    existing = await db.scalar(select(Menu.id).limit(1))
    if existing:
        return
    ordering = 0
    for doc_type, prefix, actions in DOCUMENT_TYPES:
        ordering += 1
        db.add(Menu(
            code=prefix,
            title=f"menu.{doc_type}",
            icon=doc_type,
            ordering=ordering,
            is_menu=1,
        ))
        for action in actions:
            ordering += 1
            db.add(Menu(
                parent_code=prefix,
                code=f"{prefix}.{action}",
                title=f"action.{doc_type}.{action}",
                ordering=ordering,
                is_menu=0,
            ))
    await db.flush()


async def ensure_superadmin_role(db: AsyncSession) -> Role:
    role = await db.scalar(select(Role).where(Role.nam == "SuperAdmin"))
    if not role:
        role = Role(nam="SuperAdmin", lvl=0, description="System super administrator", is_active=1)
        db.add(role)
        await db.flush()
    await replace_role_permissions(db, role.id, ALL_PERMISSIONS)
    return role


async def replace_role_permissions(db: AsyncSession, role_id: uuid.UUID, codes: list[str]) -> None:
    await db.execute(delete(Permission).where(Permission.role_id == role_id))
    for code in codes:
        db.add(Permission(role_id=role_id, code=code, is_enable=1))
    await db.flush()


async def permissions_for_role_id(db: AsyncSession, role_id: uuid.UUID | None) -> list[str]:
    if not role_id:
        return []
    rows = (await db.scalars(select(Permission.code).where(Permission.role_id == role_id, Permission.is_enable == 1))).all()
    return list(rows)


async def count_users(db: AsyncSession) -> int:
    return int(await db.scalar(select(func.count()).select_from(User)) or 0)


async def provision_first_administrator(db: AsyncSession, *, name: str, email: str, password: str) -> User:
    """Create the first account as SuperAdmin with every system permission."""
    from app.core.security import hash_password

    await db.execute(text("SELECT pg_advisory_xact_lock(87421031)"))
    if await count_users(db):
        raise DomainError("FORBIDDEN", "Registration is closed", 403)

    await seed_menus(db)
    role = await ensure_superadmin_role(db)
    user = User(
        email=email,
        name=name,
        password_hash=hash_password(password),
        role="SuperAdmin",
        permissions=list(ALL_PERMISSIONS),
        role_id=role.id,
        status="active",
        active=True,
    )
    db.add(user)
    await db.flush()
    user.created_by = user.id
    user.updated_by = user.id
    await ensure_officer_for_user(db, user, role.id)
    return user


async def ensure_officer_for_user(db: AsyncSession, user: User, role_id: uuid.UUID | None = None) -> Officer:
    officer = None
    if user.officer_id:
        officer = await db.get(Officer, user.officer_id)
    if officer is None:
        officer = await db.scalar(select(Officer).where(Officer.auth_id == user.id))
    if officer is None:
        officer = Officer(
            nam=user.name,
            email=user.email,
            auth_id=user.id,
            role_id=role_id or user.role_id,
            is_active=1 if user.active else 0,
            profile_url=user.avatar,
        )
        db.add(officer)
        await db.flush()
    else:
        officer.nam = user.name
        officer.email = user.email
        officer.auth_id = user.id
        if role_id or user.role_id:
            officer.role_id = role_id or user.role_id
        officer.is_active = 1 if user.active else 0
    user.officer_id = officer.id
    return officer


async def bind_user_officer(db: AsyncSession, user: User, officer_id: uuid.UUID) -> Officer:
    previous = await db.scalar(select(Officer).where(Officer.auth_id == user.id))
    if previous is not None and previous.id != officer_id:
        previous.auth_id = None
        await db.flush()
    officer = await db.get(Officer, officer_id)
    if officer is None:
        raise DomainError("VALIDATION_ERROR", "Linked officer does not exist or is inactive", 422)
    officer.auth_id = user.id
    user.officer_id = officer.id
    return officer


async def hydrate_user_payloads(db: AsyncSession, users: Sequence[User]) -> list[dict]:
    officer_ids = [user.officer_id for user in users if user.officer_id]
    names: dict[uuid.UUID, str] = {}
    if officer_ids:
        officers = (await db.scalars(select(Officer).where(Officer.id.in_(officer_ids)))).all()
        names = {officer.id: officer.nam for officer in officers}
    return [
        user_to_payload(user, officer_name=names.get(user.officer_id) if user.officer_id else None)
        for user in users
    ]


async def user_payload(db: AsyncSession, user: User) -> dict:
    return (await hydrate_user_payloads(db, [user]))[0]


def role_to_payload(role: Role, permissions: list[str]) -> dict:
    return {
        "id": str(role.id),
        "code": role.nam.upper().replace(" ", "_"),
        "name": role.nam,
        "description": role.description,
        "status": "active" if role.is_active else "inactive",
        "lvl": role.lvl,
        "permissions": permissions,
        "permissionCount": len(permissions),
        "createdAt": role.created_at.isoformat() if role.created_at else None,
        "updatedAt": role.updated_at.isoformat() if role.updated_at else None,
        "version": 1,
    }


def officer_to_payload(officer: Officer) -> dict:
    return {
        "id": str(officer.id),
        "name": officer.nam,
        "email": officer.email,
        "organizationId": str(officer.organization_id) if officer.organization_id else None,
        "departmentId": str(officer.organization_id) if officer.organization_id else None,
        "roleId": str(officer.role_id) if officer.role_id else None,
        "authId": str(officer.auth_id) if officer.auth_id else None,
        "profileUrl": officer.profile_url,
        "status": "active" if officer.is_active else "inactive",
        "createdAt": officer.created_at.isoformat() if officer.created_at else None,
        "updatedAt": officer.updated_at.isoformat() if officer.updated_at else None,
        "version": 1,
    }


def user_to_payload(user: User, *, officer_name: str | None = None) -> dict:
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "roleName": user.role,
        "roleId": str(user.role_id) if user.role_id else None,
        "officerId": str(user.officer_id) if user.officer_id else None,
        "officerName": officer_name,
        "avatar": user.avatar,
        "permissions": list(user.permissions or []),
        "status": user.status if user.status else ("active" if user.active else "inactive"),
        "active": user.active,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "updatedAt": user.updated_at.isoformat() if user.updated_at else None,
        "version": user.version,
    }
