from datetime import datetime, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.modules.record.model import Entity
from app.jobs.publishers import publish_tick


async def reconcile() -> None:
    await publish_tick()
