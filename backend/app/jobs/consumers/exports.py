import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.db import Entity, SessionLocal

log = logging.getLogger(__name__)


async def complete_exports() -> None:
    async with SessionLocal() as db:
        rows = (await db.scalars(select(Entity).where(Entity.resource == "export-jobs", Entity.payload["status"].as_string() == "queued").limit(10))).all()
        for row in rows:
            try:
                row.payload = {**(row.payload or {}), "status": "processing"}
                await db.flush()
                from app.modules.reporting_support.services.export import generate_export

                await generate_export(db, row)
            except Exception as exc:
                log.exception("Export job failed id=%s", row.id)
                row.payload = {**(row.payload or {}), "status": "failed", "error": str(exc)[:500], "completedAt": datetime.now(timezone.utc).isoformat()}
        await db.commit()
