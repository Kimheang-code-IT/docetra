"""storage_integration — upload validation and provider config checks."""

import pytest
from fastapi import HTTPException

from app.modules.storage_integration.domain.schemas import StorageProviderPayload
from app.modules.storage_integration.services import providers as storage_providers
from app.modules.storage_integration.services.upload_validation import detect_upload_type


def test_detect_png_and_jpeg():
    # PNG magic
    assert detect_upload_type(b"\x89PNG\r\n\x1a\n" + b"0" * 20, "png").startswith("image/")
    # JPEG magic
    assert detect_upload_type(b"\xff\xd8\xff" + b"0" * 20, "jpg").startswith("image/")


def test_detect_rejects_empty():
    with pytest.raises(HTTPException):
        detect_upload_type(b"", "pdf")


@pytest.mark.asyncio
async def test_google_drive_provider_requires_credentials():
    result = await storage_providers.test_provider({"type": "google_drive"})
    assert result["status"] == "failed"


@pytest.mark.asyncio
async def test_local_provider_disabled():
    result = await storage_providers.test_provider({"type": "local"})
    assert result["status"] == "failed"
    assert "disabled" in result["message"].lower() or "Local" in result["message"]


def test_storage_provider_schema():
    payload = StorageProviderPayload(name="minio", provider="minio", active=True)
    assert payload.name == "minio"
