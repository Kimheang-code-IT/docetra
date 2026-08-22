"""people_access — officers, users, roles, and permissions."""

from __future__ import annotations

from typing import Any

__all__ = [
    "people_service",
    "identity_service",
    "identity_sync",
    "permission_catalog",
    "notification_email",
    "notification_telegram",
]


def __getattr__(name: str) -> Any:
    if name == "people_service":
        from app.modules.people_access.services import people as people_service

        return people_service
    if name == "identity_service":
        from app.modules.people_access.services import identity as identity_service

        return identity_service
    if name == "identity_sync":
        from app.modules.people_access.services import identity_sync

        return identity_sync
    if name == "permission_catalog":
        from app.modules.people_access.services import permission_catalog

        return permission_catalog
    if name == "notification_email":
        from app.integrations import email as notification_email

        return notification_email
    if name == "notification_telegram":
        from app.integrations import telegram as notification_telegram

        return notification_telegram
    raise AttributeError(name)
