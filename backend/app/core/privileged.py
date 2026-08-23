"""Privileged role names are assigned only from the Role table, never from payloads."""

UNRESTRICTED_ROLE_NAMES = frozenset({"superadmin", "admin"})


def normalize_role_name(name: str | None) -> str:
    return "".join((name or "").split()).lower()


def is_unrestricted_role_name(name: str | None) -> bool:
    return normalize_role_name(name) in UNRESTRICTED_ROLE_NAMES


def is_unrestricted(user) -> bool:
    """True when the stored role name is a privileged system role."""
    return is_unrestricted_role_name(getattr(user, "role", None))
