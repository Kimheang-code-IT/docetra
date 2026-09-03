from datetime import datetime, timezone

from sqlalchemy import select

from app.db import SessionLocal
from app.modules.record.model import Entity


async def cleanup_expired_exports() -> None:
    now = datetime.now(timezone.utc)
    async with SessionLocal() as db:
        rows = (await db.scalars(select(Entity).where(Entity.resource == "export-jobs", Entity.payload["expiresAt"].as_string() < now.isoformat()))).all()
        from app.modules.storage_integration.service import storage

        for row in rows:
            key = (row.payload or {}).get("objectKey")
            if key:
                try:
                    await storage.delete_object(key)
                except Exception:
                    continue
            await db.delete(row)
        await db.commit()
