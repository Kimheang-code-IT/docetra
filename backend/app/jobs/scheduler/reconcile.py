from datetime import datetime, timezone

from sqlalchemy import select

from app.db import Entity, SessionLocal
from app.jobs.publishers import publish_tick


async def reconcile() -> None:
    await publish_tick()
