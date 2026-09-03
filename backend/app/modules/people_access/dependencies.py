"""Public dependency facade for People Access.

Owns current-user resolution and typed identity access. Core authentication
infrastructure stays ORM-free: the resolver below is registered into
``app.core.security`` so tokens are resolved against the People Access
``User`` model without core importing business models.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import register_user_resolver
from app.core.privileged import is_unrestricted
from app.modules.people_access.model import User

__all__ = ["current_user", "person", "public_user", "User"]


async def _resolve_user(db: AsyncSession, user_id) -> User | None:
    return await db.scalar(select(User).where(User.id == user_id, User.active.is_(True)))


register_user_resolver(_resolve_user)


# Re-exported dependency so routers consume identity from this facade.
from app.core.security import current_user  # noqa: E402


def person(user: Any | None):
    return None if not user else {"id": str(user.id), "name": user.name, "email": user.email, "avatarUrl": user.avatar}


def public_user(user: Any):
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "avatar": user.avatar,
        "permissions": user.permissions or [],
        "pageAccess": ["ALL_PAGES"] if is_unrestricted(user) else [],
    }
