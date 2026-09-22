from __future__ import annotations

import asyncio
import logging

import aio_pika
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import settings
from app.db import SessionLocal

log = logging.getLogger(__name__)
PROBE_TIMEOUT_SECONDS = 2.0


async def _probe(name: str, operation) -> str:
    try:
        async with asyncio.timeout(PROBE_TIMEOUT_SECONDS):
            await operation()
        return "ok"
    except Exception:
        log.warning("Readiness probe failed", extra={"dependency": name})
        return "unavailable"


async def probe_database() -> None:
    async with SessionLocal() as db:
        await db.execute(text("select 1"))


async def probe_redis() -> None:
    redis = Redis.from_url(settings.redis_url)
    try:
        await redis.ping()
    finally:
        await redis.aclose()


# Reuse a single probe connection: opening a fresh AMQP connection per
# readiness poll churned broker connections (FDs, memory) under frequent probes.
_rabbit_probe_connection = None


async def probe_rabbitmq() -> None:
    global _rabbit_probe_connection
    if _rabbit_probe_connection is None or _rabbit_probe_connection.is_closed:
        _rabbit_probe_connection = await aio_pika.connect(settings.rabbitmq_url)
    if _rabbit_probe_connection.is_closed:
        raise RuntimeError("rabbitmq connection closed")


async def readiness_payload(storage_probe) -> tuple[int, dict]:
    database = await _probe("database", probe_database)
    if database != "ok":
        return 503, {
            "status": "unavailable",
            "database": database,
            "redis": "skipped",
            "rabbitmq": "skipped",
            "storage": "skipped",
        }
    redis_status, rabbitmq_status, storage_status = await asyncio.gather(
        _probe("redis", probe_redis),
        _probe("rabbitmq", probe_rabbitmq),
        _probe("storage", storage_probe),
    )
    body = {
        "database": database,
        "redis": redis_status,
        "rabbitmq": rabbitmq_status,
        "storage": storage_status,
    }
    degraded = any(value != "ok" for value in body.values())
    return 200, {"status": "degraded" if degraded else "ready", **body}
