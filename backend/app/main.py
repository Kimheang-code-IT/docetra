"""Docetra process entry — API, worker, and scheduler in one module.

Run modes (still three Compose processes; one codebase entry):

- API: ``uvicorn app.main:app --host 0.0.0.0 --port 8000``
- Worker: ``python -m app.main worker``
- Scheduler: ``python -m app.main scheduler``
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager

import aio_pika
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import select, text

from app import __version__
from app.api.v2.router import router as api_router
from app.core.config import settings
from app.core.errors import DomainError
from app.core.logging import configure_logging
from app.core.metrics import observe, prometheus_response
from app.core.permissions import ALL_PERMISSIONS
from app.core.security import hash_password
from app.db import SessionLocal, User
from app.jobs.consumers import handle_message
from app.jobs.consumers.exports import complete_exports
from app.jobs.consumers.outbox import publish_outbox
from app.jobs.publishers import close_connection, publish_tick
from app.jobs.scheduler.cleanup import cleanup_expired_exports
from app.jobs.scheduler.meeting_reminders import due_meeting_reminders
from app.jobs.scheduler.reconcile import reconcile
from app.jobs.topology import DEAD_LETTER_EXCHANGE, EVENT_EXCHANGE
from app.modules.people_access.services.identity import ensure_admin_entity

configure_logging()
log = logging.getLogger(__name__)


async def seed_record_type_ui() -> None:
    """Ensure built-in record types exist with uiSurface payload for menus/API."""
    from app.modules.record.domain.map import TYPE_UI_DEFAULTS
    from app.modules.record.services.serializer import ensure_record_type

    async with SessionLocal() as db:
        for code in TYPE_UI_DEFAULTS:
            await ensure_record_type(db, code, None)
        await db.commit()


async def seed_admin() -> None:
    async with SessionLocal() as db:
        from app.modules.people_access.services.people import ensure_officer_for_user, ensure_superadmin_role, seed_menus

        try:
            await seed_menus(db)
            role = await ensure_superadmin_role(db)
        except Exception:
            log.exception("Typed role/menu seed skipped; relational migration may be pending")
            role = None

        user = await db.scalar(select(User).where(User.email == settings.admin_email.lower()))
        if not user:
            user = User(
                email=settings.admin_email.lower(),
                name=settings.admin_name,
                password_hash=hash_password(settings.admin_password),
                role="SuperAdmin",
                permissions=ALL_PERMISSIONS,
                role_id=role.id if role else None,
            )
            db.add(user)
            await db.flush()
        else:
            if not user.permissions:
                user.permissions = ALL_PERMISSIONS
            if role and not user.role_id:
                user.role_id = role.id
            user.role = "SuperAdmin"
        await ensure_admin_entity(db, user)
        try:
            await ensure_officer_for_user(db, user, role.id if role else user.role_id)
        except Exception:
            log.exception("Officer seed skipped; relational tables may be missing")
        await db.commit()


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID") or str(uuid.uuid4())


def create_app() -> FastAPI:
    is_production = settings.app_env.lower() == "production"

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings.validate_production()
        try:
            await seed_admin()
        except Exception:
            log.exception("Admin seed skipped; database may still be migrating")
        try:
            await seed_record_type_ui()
        except Exception:
            log.exception("Record type UI seed skipped; relational tables may be missing")
        yield

    application = FastAPI(
        title="Docetra API",
        version=__version__,
        openapi_url="/api/v2/openapi.json",
        docs_url=None if is_production else "/api/v2/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-Requested-With", settings.csrf_header_name],
    )
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        started = time.monotonic()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["X-Request-ID"] = request_id
        await observe(request, response.status_code, time.monotonic() - started)
        return response

    @application.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        request_id = _request_id(request)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": exc.message,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "fields": exc.fields or {},
                    "requestId": request_id,
                },
            },
            headers={"X-Request-ID": request_id},
        )

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        request_id = _request_id(request)
        message = str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": message, "error": {"code": f"HTTP_{exc.status_code}", "message": message, "fields": {}, "requestId": request_id}},
            headers={"X-Request-ID": request_id, **(exc.headers or {})},
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        request_id = _request_id(request)
        fields = [{"field": ".".join(map(str, item["loc"])), "message": item["msg"]} for item in exc.errors()]
        return JSONResponse(
            status_code=422,
            content={"message": "Validation failed", "error": {"code": "VALIDATION_ERROR", "message": "Validation failed", "fields": fields, "requestId": request_id}},
        )

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        request_id = _request_id(request)
        log.exception("Unhandled request error request_id=%s", request_id, exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error", "error": {"code": "INTERNAL_ERROR", "message": "Internal server error", "fields": {}, "requestId": request_id}},
            headers={"X-Request-ID": request_id},
        )

    @application.get("/health", tags=["health"])
    async def health():
        return {"status": "ok", "version": __version__}

    @application.get("/ready", tags=["health"])
    async def ready():
        try:
            async with SessionLocal() as db:
                await db.execute(text("select 1"))
            redis = Redis.from_url(settings.redis_url)
            await redis.ping()
            await redis.aclose()
            return {"status": "ready", "database": "ok", "redis": "ok"}
        except Exception as exc:
            raise HTTPException(503, f"Dependency unavailable: {type(exc).__name__}") from exc

    @application.get("/metrics", include_in_schema=False)
    async def metrics():
        return await prometheus_response()

    application.include_router(api_router)
    return application


app = create_app()


async def _consume(channel) -> None:
    await channel.declare_exchange(EVENT_EXCHANGE, aio_pika.ExchangeType.TOPIC, durable=True)
    await channel.declare_exchange(DEAD_LETTER_EXCHANGE, aio_pika.ExchangeType.FANOUT, durable=True)
    queue = await channel.declare_queue("docetra.work", durable=True, arguments={"x-dead-letter-exchange": DEAD_LETTER_EXCHANGE})
    await queue.bind(EVENT_EXCHANGE, routing_key="#")
    await queue.consume(handle_message)


async def run_worker() -> None:
    while True:
        try:
            connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            async with connection:
                channel = await connection.channel(publisher_confirms=True)
                await channel.set_qos(prefetch_count=8)
                await _consume(channel)
                while True:
                    await publish_outbox(channel)
                    await complete_exports()
                    await asyncio.sleep(2)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Worker connection failed; retrying")
            await asyncio.sleep(5)


async def run_scheduler() -> None:
    scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)
    scheduler.add_job(reconcile, "interval", minutes=15, id="reconcile", coalesce=True, max_instances=1)
    scheduler.add_job(due_meeting_reminders, "interval", minutes=1, id="meeting-reminders", coalesce=True, max_instances=1)
    scheduler.add_job(cleanup_expired_exports, "interval", hours=1, id="export-cleanup", coalesce=True, max_instances=1)
    scheduler.start()
    await publish_tick()
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        scheduler.shutdown(wait=False)
        await close_connection()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="app.main", description="Docetra API / worker / scheduler")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=("api", "worker", "scheduler"),
        default="api",
        help="Process role (default: api — use uvicorn for HTTP in production)",
    )
    args = parser.parse_args(argv)
    if args.mode == "worker":
        asyncio.run(run_worker())
        return
    if args.mode == "scheduler":
        asyncio.run(run_scheduler())
        return
    # api mode without uvicorn is uncommon; print guidance
    print("API mode: run with uvicorn, e.g. uvicorn app.main:app --host 0.0.0.0 --port 8000", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
