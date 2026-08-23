"""Object storage — uses default active Settings storage provider, else env MinIO."""

from __future__ import annotations

import asyncio
import re
from io import BytesIO

from minio import Minio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.secrets import reveal_mapping
from app.db import Entity
from app.db.session import SessionLocal

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
        rows = (
            await session.scalars(
                select(Entity).where(Entity.resource == "storage-providers", Entity.status != "deleted")
            )
        ).all()
        default = None
        active = None
        for row in rows:
            payload = reveal_mapping(dict(row.payload or {}))
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
    storage, bucket = await resolve_storage(db)
    exists = await asyncio.to_thread(storage.bucket_exists, bucket)
    if not exists:
        await asyncio.to_thread(storage.make_bucket, bucket)


_MISSING_OBJECT_CODES = frozenset({"NoSuchKey", "NoSuchObject", "NoSuchBucket", "NotFound"})


async def put_bytes(key: str, data: bytes, content_type: str, db: AsyncSession | None = None, *, attempts: int = 3):
    last_error: BaseException | None = None
    for attempt in range(1, max(1, attempts) + 1):
        try:
            storage, bucket = await resolve_storage(db)
            await ensure_bucket(db)
            await asyncio.to_thread(storage.put_object, bucket, key, BytesIO(data), len(data), content_type=content_type)
            return
        except Exception as exc:
            last_error = exc
            if attempt >= attempts:
                break
            await asyncio.sleep(0.15 * (2 ** (attempt - 1)))
    assert last_error is not None
    raise last_error


async def delete_object(key: str, db: AsyncSession | None = None, *, missing_ok: bool = True):
    if not key:
        return
    storage, bucket = await resolve_storage(db)
    try:
        await asyncio.to_thread(storage.remove_object, bucket, key)
    except Exception as exc:
        code = str(getattr(exc, "code", "") or "")
        if missing_ok and code in _MISSING_OBJECT_CODES:
            return
        raise


def _read_object(storage: Minio, bucket: str, key: str) -> bytes:
    response = storage.get_object(bucket, key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


async def get_object_bytes(key: str, db: AsyncSession | None = None) -> bytes:
    storage, bucket = await resolve_storage(db)
    return await asyncio.to_thread(_read_object, storage, bucket, key)


def safe_name(value: str):
    return re.sub(r"[^A-Za-z0-9._-]", "_", value)[:180] or "file"
