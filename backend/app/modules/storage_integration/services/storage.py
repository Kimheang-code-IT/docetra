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
