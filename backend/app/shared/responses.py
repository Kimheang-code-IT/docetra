"""API envelope builders matching frontend contract shapes."""

from __future__ import annotations

from typing import Any

from app.shared.pagination import page_meta


def data_envelope(data: Any, *, meta: dict[str, Any] | None = None, errors: list | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"data": data}
    if meta is not None:
        payload["meta"] = meta
    if errors is not None:
        payload["errors"] = errors
    return payload


def list_envelope(items: list[Any], *, page: int, limit: int, total: int) -> dict[str, Any]:
    return data_envelope(items, meta=page_meta(page, limit, total))
