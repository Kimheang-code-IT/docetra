import json
from datetime import datetime, timezone

import aio_pika

from app.core.config import settings
from app.jobs.topology import EVENT_EXCHANGE

_connection = None


async def publish(routing_key: str, payload: dict) -> None:
    global _connection
    if not _connection or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await _connection.channel(publisher_confirms=True)
    exchange = await channel.declare_exchange(EVENT_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    await exchange.publish(
        aio_pika.Message(json.dumps(payload).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
        routing_key=routing_key,
    )


async def publish_tick() -> None:
    await publish("scheduler.reconcile", {"occurredAt": datetime.now(timezone.utc).isoformat(), "kind": "scheduler.reconcile"})


async def close_connection() -> None:
    global _connection
    if _connection:
        await _connection.close()
        _connection = None
