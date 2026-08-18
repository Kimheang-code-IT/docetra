from sqlalchemy.ext.asyncio import AsyncSession
from app.db import Outbox
def add_event(db: AsyncSession, topic: str, payload: dict): db.add(Outbox(topic=topic,payload=payload))
