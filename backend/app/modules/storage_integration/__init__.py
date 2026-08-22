"""storage_integration — file upload, object storage, and Google Drive synchronization."""

from __future__ import annotations

from typing import Any

__all__ = [
    "storage_service",
    "storage_providers",
    "storage_provider_service",
    "upload_validation",
    "google_drive_service",
    "drive_sync_service",
]


def __getattr__(name: str) -> Any:
    if name == "storage_service":
        from app.modules.storage_integration.services import storage as storage_service

        return storage_service
    if name == "storage_providers":
        from app.modules.storage_integration.services import providers as storage_providers

        return storage_providers
    if name == "storage_provider_service":
        from app.modules.storage_integration.services import provider_service as storage_provider_service

        return storage_provider_service
    if name == "upload_validation":
        from app.modules.storage_integration.services import upload_validation

        return upload_validation
    if name == "google_drive_service":
        from app.integrations import google as google_drive_service

        return google_drive_service
    if name == "drive_sync_service":
        from app.modules.storage_integration.services import drive_sync as drive_sync_service

        return drive_sync_service
    raise AttributeError(name)
