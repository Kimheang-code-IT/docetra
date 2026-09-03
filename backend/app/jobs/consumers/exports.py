import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, select

from app.core.config import settings
from app.db import SessionLocal
from app.modules.record.model import Entity

log = logging.getLogger(__name__)

LOCK_TTL_SECONDS = 15 * 60
STATUS_CACHE_TTL_SECONDS = 60


def _lock_key(job_id: str) -> str:
    return f"export-job-lock:{job_id}"


def _status_key(job_id: str) -> str:
    return f"export-job:{job_id}"


def _cache_payload(row: Entity) -> dict:
    # Same envelope the API writes so GET /exports/{id} can serve either side's writes.
    from app.modules.record.service import stamp

    return {"ownerId": str(row.created_by or ""), "data": stamp(row)}


async def _cache_status(row: Entity) -> None:
    try:
        from app.core.cache import short_cache

        await short_cache.set(_status_key(str(row.id)), _cache_payload(row), STATUS_CACHE_TTL_SECONDS)
    except Exception:
        log.debug("Export status cache write failed id=%s", row.id)


async def _drop_status(job_id: str) -> None:
    try:
        from app.core.cache import short_cache

        await short_cache.delete(_status_key(job_id))
    except Exception:
        pass


async def _acquire_lock(job_id: str) -> bool:
    """Redis NX lock so the MQ consumer and the poll loop never double-run a job."""
    try:
        from app.core.cache import short_cache

        return await short_cache.add(_lock_key(job_id), job_id, LOCK_TTL_SECONDS)
    except Exception:
        return True


async def _release_lock(job_id: str) -> None:
    try:
        from app.core.cache import short_cache

        await short_cache.delete(_lock_key(job_id))
    except Exception:
        pass


async def _execute(db, row: Entity) -> None:
    payload = dict(row.payload or {})
    if payload.get("status") in {"completed", "pending_purge"}:
        return
    job_id = str(row.id)
    if not await _acquire_lock(job_id):
        return
    try:
        if int(payload.get("attempts") or 0) >= settings.job_max_retries:
            row.payload = {**payload, "status": "failed", "error": "Max export attempts reached"}
            await db.flush()
            await _cache_status(row)
            return
        row.payload = {**payload, "status": "processing", "attempts": int(payload.get("attempts") or 0) + 1}
        await db.flush()
        await _cache_status(row)

        from app.modules.reporting_support.service import export

        await export.generate_export(db, row)
        await db.flush()
        await _cache_status(row)
    except Exception as exc:
        log.exception("Export job failed id=%s", job_id)
        row.payload = {
            **(row.payload or {}),
            "status": "failed",
            "error": str(exc)[:500],
            "completedAt": datetime.now(timezone.utc).isoformat(),
        }
        await db.flush()
        await _cache_status(row)
    finally:
        await _release_lock(job_id)


async def handle_export_execute(message: dict) -> None:
    """RabbitMQ consumer for topic ``export.execute`` published by the API outbox."""
    raw = message.get("jobId")
    try:
        job_id = uuid.UUID(str(raw))
    except (ValueError, TypeError):
        log.warning("Export message without valid jobId: %s", raw)
        return
    async with SessionLocal() as db:
        row = await db.get(Entity, job_id)
        if not row or row.resource != "export-jobs":
            log.warning("Export job missing id=%s", raw)
            return
        await _execute(db, row)
        await db.commit()


async def complete_exports() -> None:
    """Safety net: run queued jobs whose outbox message was lost, and recover stale processing rows."""
    stale_before = datetime.now(timezone.utc) - timedelta(minutes=5)
    async with SessionLocal() as db:
        status = Entity.payload["status"].as_string()
        rows = (await db.scalars(select(Entity).where(
            Entity.resource == "export-jobs",
            or_(
                status == "queued",
                and_(status == "processing", Entity.updated_at < stale_before),
            ),
        ).limit(10))).all()
        for row in rows:
            await _execute(db, row)
        await db.commit()
