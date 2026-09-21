"""Object storage — uses default active Settings storage provider, else env MinIO."""

from __future__ import annotations

import asyncio

from minio import Minio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.secrets import reveal_mapping
from app.db.session import SessionLocal
from app.integrations import objectstore
from app.modules.record.service import entity_bags

_client: Minio | None = None
_bucket: str | None = None


def _env_client() -> tuple[Minio, str]:
    client = Minio(
        settings.s3_endpoint.removeprefix("http://").removeprefix("https://"),
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        secure=settings.s3_use_ssl,
    )
    return client, settings.s3_bucket


def _client_from_payload(payload: dict) -> tuple[Minio, str] | None:
    kind = str(payload.get("type") or "minio").lower()
    if kind not in {"minio", "amazon_s3", "cloudflare_r2", "s3"}:
        return None
    endpoint = str(payload.get("endpoint") or settings.s3_endpoint).removeprefix("http://").removeprefix("https://")
    if not endpoint:
        return None
    secure = bool(payload.get("useSsl", payload.get("ssl", settings.s3_use_ssl)))
    client = Minio(
        endpoint,
        access_key=str(payload.get("accessKey") or settings.s3_access_key),
        secret_key=str(payload.get("secretKey") or settings.s3_secret_key),
        secure=secure,
        region=payload.get("region") or None,
    )
    bucket = str(payload.get("bucket") or settings.s3_bucket)
    return client, bucket


async def resolve_storage(db: AsyncSession | None = None) -> tuple[Minio, str]:
    global _client, _bucket
    if _client is not None and _bucket:
        return _client, _bucket

    async def _load(session: AsyncSession) -> tuple[Minio, str]:
        rows = await entity_bags.list_entities(session, "storage-providers")
        default = None
        active = None
        for row in rows:
            if row["status"] == "deleted":
                continue
            payload = reveal_mapping(row["payload"])
            if not payload.get("active", True):
                continue
            if payload.get("isDefault"):
                default = payload
                break
            if active is None:
                active = payload
        chosen = default or active
        if chosen:
            built = await asyncio.to_thread(_client_from_payload, chosen)
            if built:
                return built
        return await asyncio.to_thread(_env_client)

    if db is not None:
        client, bucket = await _load(db)
    else:
        async with SessionLocal() as session:
            client, bucket = await _load(session)
    _client, _bucket = client, bucket
    return client, bucket


async def invalidate_storage_client() -> None:
    global _client, _bucket
    _client = None
    _bucket = None


_S3_KINDS = {"minio", "amazon_s3", "cloudflare_r2", "s3"}


async def storage_status(db: AsyncSession) -> dict:
    """Read-only storage readiness for portal users (never reveals secret material).

    A UI-configured provider wins; otherwise the env MinIO/S3 values count as the
    ready fallback. Google Drive is ready when a configured source exists or the
    env access token + folder are set.
    """
    rows = await entity_bags.list_entities(db, "storage-providers")

    file_provider = None
    fallback_file = None
    drive_provider = None
    for row in rows:
        if row["status"] == "deleted":
            continue
        payload = row["payload"] or {}
        if not payload.get("active", True):
            continue
        kind = str(payload.get("type") or "minio").lower()
        if kind == "google_drive":
            if drive_provider is None and payload.get("folderId"):
                drive_provider = payload
            continue
        if kind in _S3_KINDS:
            if payload.get("isDefault"):
                file_provider = payload
                break
            if fallback_file is None:
                fallback_file = payload
    file_provider = file_provider or fallback_file

    env_file_ready = bool(settings.s3_endpoint and settings.s3_access_key and settings.s3_secret_key and settings.s3_bucket)
    if file_provider is not None:
        file_storage = {
            "ready": True,
            "source": "provider",
            "providerType": str(file_provider.get("type") or "minio").lower(),
            "bucket": file_provider.get("bucket") or settings.s3_bucket,
            "endpoint": file_provider.get("endpoint") or settings.s3_endpoint,
        }
    elif env_file_ready:
        file_storage = {
            "ready": True,
            "source": "environment",
            "providerType": "minio",
            "bucket": settings.s3_bucket,
            "endpoint": settings.s3_endpoint,
        }
    else:
        file_storage = {"ready": False, "source": "none", "providerType": None, "bucket": None, "endpoint": None}

    env_drive_ready = bool(settings.google_drive_access_token and settings.google_drive_folder_id)
    if drive_provider is not None:
        drive_source = "provider"
    elif env_drive_ready:
        drive_source = "environment"
    else:
        drive_source = "none"
    google_drive = {
        "ready": drive_provider is not None or env_drive_ready,
        "source": drive_source,
        "folderId": (drive_provider or {}).get("folderId") or (settings.google_drive_folder_id or None),
    }
    return {"fileStorage": file_storage, "googleDrive": google_drive}


async def ensure_bucket(db: AsyncSession | None = None):
    return await objectstore.ensure_bucket(db, resolver=resolve_storage)


async def put_bytes(
    key: str,
    data: bytes,
    content_type: str,
    db: AsyncSession | None = None,
    *,
    attempts: int = 3,
):
    return await objectstore.put_bytes(
        key,
        data,
        content_type,
        db,
        attempts=attempts,
        resolver=resolve_storage,
        bucket_ensurer=ensure_bucket,
    )


async def delete_object(key: str, db: AsyncSession | None = None, *, missing_ok: bool = True):
    return await objectstore.delete_object(
        key,
        db,
        missing_ok=missing_ok,
        resolver=resolve_storage,
    )


async def get_object_bytes(key: str, db: AsyncSession | None = None) -> bytes:
    return await objectstore.get_object_bytes(key, db, resolver=resolve_storage)


safe_name = objectstore.safe_name
