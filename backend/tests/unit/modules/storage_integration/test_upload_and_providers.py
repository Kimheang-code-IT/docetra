"""storage_integration — upload validation and provider config checks."""

import pytest
from fastapi import HTTPException

from app.modules.storage_integration.domain.schemas import StorageProviderPayload
from app.modules.storage_integration.services import providers as storage_providers
from app.modules.storage_integration.services.storage import _choose_file_provider
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


def test_choose_file_provider_prefers_s3_over_minio_default():
    minio_default = {"type": "minio", "isDefault": True, "active": True}
    s3_active = {"type": "amazon_s3", "active": True}
    assert _choose_file_provider([minio_default, s3_active]) is s3_active


def test_choose_file_provider_falls_back_to_minio_without_s3():
    minio = {"type": "minio", "active": True}
    assert _choose_file_provider([minio]) is minio


def test_choose_file_provider_ignores_inactive_and_non_s3():
    assert _choose_file_provider([{"type": "amazon_s3", "active": False}]) is None
    assert _choose_file_provider([{"type": "google_drive", "active": True}]) is None
