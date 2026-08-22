"""Non-domain field validators."""

from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def nonempty(value: str | None, *, field: str = "value") -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field} is required")
    return text


def is_email(value: str | None) -> bool:
    if not value:
        return False
    return bool(_EMAIL_RE.match(value.strip()))


def require_email(value: str | None, *, field: str = "email") -> str:
    text = nonempty(value, field=field)
    if not is_email(text):
        raise ValueError(f"{field} is invalid")
    return text
