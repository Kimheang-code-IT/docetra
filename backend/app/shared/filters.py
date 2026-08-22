"""Shared list-query parsing helpers."""

from __future__ import annotations

from typing import Any

from app.shared.pagination import parse_limit


def parse_list_query(
    params: dict[str, Any] | None,
    *,
    default_limit: int = 20,
    cap: int = 100,
) -> dict[str, Any]:
    raw = dict(params or {})
    page = max(1, int(raw.get("page") or 1))
    limit = parse_limit(str(raw.get("limit")) if raw.get("limit") is not None else None, default=default_limit, cap=cap)
    return {
        "page": page,
        "limit": limit,
        "q": (raw.get("q") or "").strip() or None,
        "status": raw.get("status"),
        "stage": raw.get("stage"),
        "sort": raw.get("sort") or "-updatedAt",
        "startDate": raw.get("startDate"),
        "endDate": raw.get("endDate"),
        "extra": {k: v for k, v in raw.items() if k not in {"page", "limit", "q", "status", "stage", "sort", "startDate", "endDate"}},
    }
