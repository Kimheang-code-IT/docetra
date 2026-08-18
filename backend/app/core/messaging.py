import json
import aio_pika
from app.core.config import settings
async def publish(topic: str, payload: dict):
    connection=await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel=await connection.channel(publisher_confirms=True); exchange=await channel.declare_exchange("docetra.events",aio_pika.ExchangeType.TOPIC,durable=True)
        await exchange.publish(aio_pika.Message(json.dumps(payload).encode(),delivery_mode=aio_pika.DeliveryMode.PERSISTENT),routing_key=topic)
