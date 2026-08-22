"""Reusable cross-module helpers. Prefer ``app.shared`` over copying utils into modules."""

from app.shared.ids import as_uuid, get_or_404
from app.shared.pagination import page_meta, paginate, parse_limit

__all__ = [
    "as_uuid",
    "get_or_404",
    "page_meta",
    "paginate",
    "parse_limit",
]
