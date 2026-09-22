import asyncio
import json
from datetime import datetime, timezone

import aio_pika

from app.core.config import settings
from app.jobs.topology import EVENT_EXCHANGE

_connection = None
_channel = None
# aio_pika channels are not safe for concurrent use; serialize publishes.
_lock = asyncio.Lock()


async def _get_channel():
    """Reuse one publisher channel. Opening a channel per publish leaked
    channels on the long-lived connection and drove RabbitMQ memory/CPU up."""
    global _connection, _channel
    if _channel is not None and not _channel.is_closed:
        if _connection is not None and not _connection.is_closed:
            return _channel
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    _channel = await _connection.channel(publisher_confirms=True)
    return _channel


async def publish(routing_key: str, payload: dict) -> None:
    async with _lock:
        channel = await _get_channel()
        exchange = await channel.declare_exchange(EVENT_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
        await exchange.publish(
            aio_pika.Message(json.dumps(payload).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key=routing_key,
        )


async def publish_tick() -> None:
    await publish("scheduler.reconcile", {"occurredAt": datetime.now(timezone.utc).isoformat(), "kind": "scheduler.reconcile"})


async def close_connection() -> None:
    global _connection, _channel
    if _channel is not None:
        try:
            await _channel.close()
        except Exception:
            pass
        _channel = None
    if _connection:
        await _connection.close()
        _connection = None
