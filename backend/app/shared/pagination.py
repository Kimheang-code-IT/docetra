"""Pagination helpers shared by module repositories and list endpoints."""

from __future__ import annotations

import math
from typing import Any, Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


def parse_limit(raw: str | None, *, default: int = 20, cap: int = 100) -> int:
    if raw in {"all", "-1"}:
        return cap
    try:
        return min(cap, max(1, int(raw or default)))
    except ValueError:
        return default


def page_meta(page: int, limit: int, total: int) -> dict[str, int]:
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": max(1, math.ceil(total / limit) if limit else 1),
    }


async def paginate(db: AsyncSession, stmt: Select[Any], *, page: int, limit: int) -> tuple[Sequence[Any], int]:
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = await db.scalar(count_stmt) or 0
    rows = (await db.scalars(stmt.offset((page - 1) * limit).limit(limit))).all()
    return rows, int(total)
