"""UUID parsing and primary-key lookups."""

from __future__ import annotations

import uuid
from typing import TypeVar

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


def as_uuid(value: str, *, not_found: str = "Not found") -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except ValueError as exc:
        raise HTTPException(404, not_found) from exc


async def get_or_404(
    db: AsyncSession,
    model: type[T],
    entity_id: str | uuid.UUID,
    *,
    not_found: str = "Not found",
) -> T:
    uid = entity_id if isinstance(entity_id, uuid.UUID) else as_uuid(str(entity_id), not_found=not_found)
    row = await db.get(model, uid)
    if not row:
        raise HTTPException(404, not_found)
    return row
