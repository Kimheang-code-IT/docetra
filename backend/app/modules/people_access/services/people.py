"""People/access helpers: menu seed, role permissions, officer linkage."""

import uuid
from collections.abc import Sequence

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.core.permissions import ALL_PERMISSIONS, DOCUMENT_TYPES, PREFIXES
from app.modules.people_access.model import Menu, Officer, Permission, Role, User
from app.modules.people_access.repository import PeopleAccessRepository


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


from app.core.permissions import catalog_rows


async def replace_role_permissions(db: AsyncSession, role_id: uuid.UUID, codes: list[str], creator_scoped: set[str] | None = None) -> None:
    """Replace a role's permission rows; ``creator_scoped`` codes get scope='creator'."""
    creator = creator_scoped or set()
    await db.execute(delete(Permission).where(Permission.role_id == role_id))
    for code in codes:
        db.add(Permission(role_id=role_id, code=code, is_enable=1, scope="creator" if code in creator else "all"))
    await db.flush()


async def creator_scoped_codes_for_role(db: AsyncSession, role_id: uuid.UUID | None) -> set[str]:
    """Enabled permission codes carrying creator scope for this role."""
    if not role_id:
        return set()
    rows = (await db.scalars(
        select(Permission.code).where(Permission.role_id == role_id, Permission.is_enable == 1, Permission.scope == "creator")
    )).all()
    return set(rows)


async def creator_scoped_actions_for_prefix(db: AsyncSession, role_id: uuid.UUID | None, prefix: str) -> set[str]:
    """Enabled `prefix.action` codes carrying creator scope for this role."""
    if not role_id or not prefix:
        return set()
    rows = (await db.scalars(
        select(Permission).where(
            Permission.role_id == role_id,
            Permission.is_enable == 1,
            Permission.code.like(f"{prefix}.%"),
        )
    )).all()
    return {row.code for row in rows if row.scope == "creator"}


def creator_scoped_codes_from_rows(permission_rows: list | None) -> set[str]:
    """Flatten onlyIfCreator document-type rows into `prefix.action` codes."""
    from app.core.permissions import TYPE_TO_PREFIX

    keys: set[str] = set()
    for row in permission_rows or []:
        if not isinstance(row, dict) or not row.get("onlyIfCreator"):
            continue
        prefix = TYPE_TO_PREFIX.get(str(row.get("documentType") or ""))
        if not prefix:
            continue
        for action in row.get("actions") or []:
            keys.add(f"{prefix}.{action}")
    return keys


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


async def officer_organization_id(
    db: AsyncSession,
    officer_id: uuid.UUID | None,
) -> uuid.UUID | None:
    if officer_id is None:
        return None
    officer = await PeopleAccessRepository(db).officer(officer_id)
    return officer.organization_id if officer else None


async def officer_ids_for_organization(
    db: AsyncSession,
    organization_id: uuid.UUID,
) -> list[uuid.UUID]:
    """Expose organization membership without leaking the Officer model."""
    rows = await db.scalars(
        select(Officer.id).where(Officer.organization_id == organization_id)
    )
    return list(rows.all())


async def officer_names_by_ids(db: AsyncSession, officer_ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
    """Batched officer display names for audit actor enrichment."""
    ids = {uid for uid in officer_ids if uid}
    if not ids:
        return {}
    rows = (await db.scalars(select(Officer).where(Officer.id.in_(ids)))).all()
    return {row.id: row.nam for row in rows if row.nam}


async def public_users_by_ids(db: AsyncSession, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, dict]:
    if not user_ids:
        return {}
    rows = (await db.scalars(select(User).where(User.id.in_(user_ids)))).all()
    return {
        row.id: {"id": str(row.id), "name": row.name, "email": row.email, "avatarUrl": row.avatar}
        for row in rows
    }


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


def role_to_payload(role: Role, permissions: list[str], creator_scoped: set[str] | None = None) -> dict:
    from app.core.permissions import normalize_permission_payload

    creator = creator_scoped or set()
    permission_rows = []
    for row in catalog_rows():
        prefix = row["permissionPrefix"]
        actions = [a for a in row["actions"] if f"{prefix}.{a}" in set(permissions)]
        if not actions:
            continue
        permission_rows.append({
            "documentType": row["documentType"],
            "actions": actions,
            "onlyIfCreator": any(f"{prefix}.{a}" in creator for a in actions),
            "level": row["level"],
        })
    normalized = normalize_permission_payload({
        "permissionRows": permission_rows,
        "permissions": sorted(set(permissions)),
    })
    return {
        "id": str(role.id),
        "code": role.nam.upper().replace(" ", "_"),
        "name": role.nam,
        "description": role.description,
        "status": "active" if role.is_active else "inactive",
        "lvl": role.lvl,
        "permissions": normalized["permissions"],
        "permissionRows": normalized["permissionRows"],
        "permissionCount": normalized["permissionCount"],
        "permissionSchemaVersion": normalized["permissionSchemaVersion"],
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
