"""Shared list-query helpers: sort + date-range contract for collection lists.

The frontend list contract is:
    page, limit, q, status, sort (-key for desc), startDate, endDate
Backends must implement these or the frontend must not send them; silent
ignoring of an active UI filter is not allowed.
"""

from __future__ import annotations

import re

from sqlalchemy.sql.elements import ColumnElement

from app.core.datetime import parse_instant


def _snake_case(key: str) -> str:
    """`updatedAt` → `updated_at` (frontend sort keys are camelCase)."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", key).lower()


def order_clause(
    params: dict,
    model,
    *,
    allowed: set[str] | None = None,
    default: str = "updatedAt",
    column_map: dict[str, str] | None = None,
) -> ColumnElement:
    """Build an ORDER BY clause from the `sort` param (e.g. `-updatedAt`).

    Keys are matched against ``column_map`` (camelCase → attribute name) or
    against the model's snake_case attributes; unknown keys fall back to
    ``default`` so clients cannot sort on arbitrary columns.
    """
    sort = str(params.get("sort") or f"-{default}")
    desc = sort.startswith("-")
    key = sort.lstrip("-")
    attribute = (column_map or {}).get(key) or _snake_case(key)
    if allowed is not None and key not in allowed:
        attribute = (column_map or {}).get(default) or _snake_case(default)
        key = default
    column = getattr(model, attribute, None)
    if column is None:
        column = getattr(model, _snake_case(default))
        desc = True
    return column.desc() if desc else column.asc()


def date_filters(params: dict, column, *, start_key: str = "startDate", end_key: str = "endDate") -> list:
    """Build inclusive date-range filters from `startDate`/`endDate` params."""
    start = parse_instant(params.get(start_key))
    end = parse_instant(params.get(end_key), end_of_day=True)
    out: list = []
    if start:
        out.append(column >= start)
    if end:
        out.append(column <= end)
    return out
