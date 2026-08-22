"""People/access helpers: menu seed, role permissions, officer linkage."""

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

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


def user_to_payload(user: User) -> dict:
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "roleName": user.role,
        "roleId": str(user.role_id) if user.role_id else None,
        "officerId": str(user.officer_id) if user.officer_id else None,
        "avatar": user.avatar,
        "permissions": list(user.permissions or []),
        "status": user.status if user.status else ("active" if user.active else "inactive"),
        "active": user.active,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "updatedAt": user.updated_at.isoformat() if user.updated_at else None,
        "version": user.version,
    }
