import json
import logging
import uuid
from datetime import datetime, timezone

import aio_pika
from sqlalchemy import select

from app.core.config import settings
from app.core.secrets import reveal_mapping
from app.db import SessionLocal
from app.modules.admin_config.model import AppSetting
from app.modules.record.model import Entity
from app.platform.messaging.model import Outbox

log = logging.getLogger(__name__)


async def publish_outbox(channel) -> None:
    from app.jobs.topology import EVENT_EXCHANGE

    exchange = await channel.declare_exchange(EVENT_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    async with SessionLocal() as db:
        rows = (await db.scalars(select(Outbox).where(Outbox.processed_at.is_(None)).order_by(Outbox.created_at).limit(100))).all()
        for row in rows:
            try:
                message = aio_pika.Message(json.dumps(row.payload).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT, message_id=str(row.id))
                await exchange.publish(message, routing_key=row.topic)
                row.processed_at = datetime.now(timezone.utc)
                row.attempts += 1
            except Exception:
                log.exception("Outbox publish failed topic=%s id=%s", row.topic, row.id)
                row.attempts += 1
                if row.attempts >= settings.job_max_retries:
                    row.processed_at = datetime.now(timezone.utc)
                    db.add(Entity(resource="system-logs", payload={"level": "error", "action": "outbox.failed", "outboxId": str(row.id), "topic": row.topic, "attempts": row.attempts, "occurredAt": datetime.now(timezone.utc).isoformat()}, status="active"))
        await db.commit()
