"""Vendor object-store operations with an application-supplied resolver."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from io import BytesIO
from typing import Any


StorageResolver = Callable[[Any | None], Awaitable[tuple[Any, str]]]

_resolver: StorageResolver | None = None
_MISSING_OBJECT_CODES = frozenset({"NoSuchKey", "NoSuchObject", "NoSuchBucket", "NotFound"})


def configure_objectstore(resolver: StorageResolver) -> None:
    global _resolver
    _resolver = resolver


async def _resolve(context=None, *, resolver: StorageResolver | None = None) -> tuple[Any, str]:
    selected = resolver or _resolver
    if selected is None:
        raise RuntimeError("Object-store resolver has not been configured")
    return await selected(context)


async def ensure_bucket(context=None, *, resolver: StorageResolver | None = None) -> None:
    client, bucket = await _resolve(context, resolver=resolver)
    if not await asyncio.to_thread(client.bucket_exists, bucket):
        await asyncio.to_thread(client.make_bucket, bucket)


async def put_bytes(
    key: str,
    data: bytes,
    content_type: str,
    context=None,
    *,
    attempts: int = 3,
    resolver: StorageResolver | None = None,
    bucket_ensurer=None,
) -> None:
    last_error: BaseException | None = None
    for attempt in range(1, max(1, attempts) + 1):
        try:
            client, bucket = await _resolve(context, resolver=resolver)
            if bucket_ensurer is None:
                await ensure_bucket(context, resolver=resolver)
            else:
                await bucket_ensurer(context)
            await asyncio.to_thread(
                client.put_object,
                bucket,
                key,
                BytesIO(data),
                len(data),
                content_type=content_type,
            )
            return
        except Exception as exc:
            last_error = exc
            if attempt >= attempts:
                break
            await asyncio.sleep(0.15 * (2 ** (attempt - 1)))
    assert last_error is not None
    raise last_error


async def delete_object(
    key: str,
    context=None,
    *,
    missing_ok: bool = True,
    resolver: StorageResolver | None = None,
) -> None:
    if not key:
        return
    client, bucket = await _resolve(context, resolver=resolver)
    try:
        await asyncio.to_thread(client.remove_object, bucket, key)
    except Exception as exc:
        code = str(getattr(exc, "code", "") or "")
        if missing_ok and code in _MISSING_OBJECT_CODES:
            return
        raise


def _read_object(client, bucket: str, key: str) -> bytes:
    response = client.get_object(bucket, key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


async def get_object_bytes(
    key: str,
    context=None,
    *,
    resolver: StorageResolver | None = None,
) -> bytes:
    client, bucket = await _resolve(context, resolver=resolver)
    return await asyncio.to_thread(_read_object, client, bucket, key)


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", value)[:180] or "file"


__all__ = [
    "configure_objectstore",
    "delete_object",
    "ensure_bucket",
    "get_object_bytes",
    "put_bytes",
    "safe_name",
]
