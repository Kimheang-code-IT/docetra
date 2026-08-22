"""organization — departments, government structures, companies, and related classification data."""

from __future__ import annotations

from typing import Any

__all__ = ["organization_service", "record_organization_service"]


def __getattr__(name: str) -> Any:
    if name == "organization_service":
        from app.modules.organization.services import service as organization_service

        return organization_service
    if name == "record_organization_service":
        from app.modules.organization.services import record_links as record_organization_service

        return record_organization_service
    raise AttributeError(name)
