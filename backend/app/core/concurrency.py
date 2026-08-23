"""Optimistic concurrency tokens for versioned resources."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.core.errors import DomainError

VERSIONED_KINDS = frozenset({"record", "user", "entity"})


def parse_version_token(*candidates: Any) -> int | None:
    """Return the first parseable integer version from body / If-Match / query."""
    for raw in candidates:
        if raw is None or raw == "":
            continue
        text = str(raw).strip().strip('"').removeprefix("W/")
        if not text:
            continue
        try:
            return int(text)
        except (TypeError, ValueError) as exc:
            raise DomainError("VERSION_REQUIRED", "A current version token is required", 428) from exc
    return None


def require_matching_version(current: Any, expected: Any) -> int:
    if expected is None:
        raise DomainError("VERSION_REQUIRED", "A current version token is required", 428)
    try:
        current_version = int(current)
        expected_version = int(expected)
    except (TypeError, ValueError) as exc:
        raise DomainError("VERSION_REQUIRED", "A current version token is required", 428) from exc
    if expected_version != current_version:
        raise DomainError("VERSION_CONFLICT", "Record was changed by another user", 409)
    return expected_version


def header_match(headers: Mapping[str, str] | None) -> str | None:
    if not headers:
        return None
    for key, value in headers.items():
        if key.lower() == "if-match":
            return value
    return None
