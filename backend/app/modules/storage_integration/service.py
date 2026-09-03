"""Public application-service facade for Storage Integration."""

import asyncio

from app.modules.storage_integration.services import drive_sync, provider_service, storage
from app.modules.storage_integration.services.reporting import read_for_reporting, search_for_reporting
from app.modules.storage_integration.services.file_collection import StorageFileCollectionService


async def probe_storage() -> None:
    client, bucket = await storage.resolve_storage()
    await asyncio.to_thread(client.bucket_exists, bucket)

__all__ = ["StorageFileCollectionService", "drive_sync", "probe_storage", "provider_service", "read_for_reporting", "search_for_reporting", "storage"]
