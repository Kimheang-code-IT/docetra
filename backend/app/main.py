"""Docetra process entry — API, worker, scheduler, and Telegram bot.

Run modes (one codebase entry):

- API: ``uvicorn app.main:app --host 0.0.0.0 --port 8000``
- Worker: ``python -m app.main worker``
- Scheduler: ``python -m app.main scheduler``
- Telegram: ``python -m app.main telegram`` (long-polling bot, dedicated process)

Small single-box deployments may set ``SCHEDULER_IN_API=true`` to run the
APScheduler jobs inside the API process and skip the scheduler container.
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
from app import __version__
from app.api.v2.router import router as api_router
from app.core.config import settings
from app.core.errors import DomainError
from app.core.logging import bind_request_context, configure_logging, reset_request_context
from app.core.metrics import observe, prometheus_response
from app.core.readiness import readiness_payload
from app.db import SessionLocal
from app.modules.people_access import dependencies as _people_access_dependencies  # noqa: F401 - registers identity resolver
from app.modules.organization.service import names_by_ids
from app.modules.people_access.services import people as _people_service

# Composition-root wiring: officer organization-name resolution comes from the
# organization public facade via injection (keeps people_access → organization
# out of the module dependency graph).
_people_service.register_organization_names_resolver(names_by_ids)
from app.jobs.consumers import handle_message
from app.jobs.consumers.exports import complete_exports
from app.jobs.consumers.outbox import publish_outbox
from app.jobs.publishers import close_connection, publish_tick
from app.jobs.scheduler.cleanup import cleanup_expired_exports
from app.jobs.scheduler.meeting_reminders import due_meeting_reminders
from app.jobs.scheduler.reconcile import reconcile
from app.jobs.topology import DEAD_LETTER_EXCHANGE, EVENT_EXCHANGE
from app.modules.people_access.service import ensure_superadmin_role
from app.modules.storage_integration.service import probe_storage

configure_logging()
log = logging.getLogger(__name__)

API_CONTENT_SECURITY_POLICY = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
# Swagger UI is dev-only (docs_url disabled in production) but still locked down:
# CDN assets for swagger-ui-dist, inline init script/styles, same-origin openapi fetch.
DOCS_CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "font-src 'self' data: https://cdn.jsdelivr.net; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'self'"
)
DOCS_PATHS = frozenset({"/api/v2/docs", "/api/v2/openapi.json"})


async def seed_system() -> None:
    """Seed the SuperAdmin role only. Record types, menus, and users are never
    auto-created — administrators build them through the UI.

    The first administrator is inserted through ``POST /api/v2/auth/register``
    (registration closes once any user exists); later accounts are created
    through the users API.
    """
    async with SessionLocal() as db:
        try:
            await ensure_superadmin_role(db)
        except Exception:
            log.exception("SuperAdmin role seed skipped; relational migration may be pending")
        await db.commit()


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID") or str(uuid.uuid4())


def create_app() -> FastAPI:
    is_production = settings.app_env.lower() == "production"

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        settings.validate_production()
        try:
            await seed_system()
        except Exception:
            log.exception("System seed skipped; database may still be migrating")
        # Optional in-process scheduler for small single-process deployments.
        scheduler: AsyncIOScheduler | None = None
        if settings.scheduler_in_api:
            log.warning("SCHEDULER_IN_API=true: running APScheduler inside the API process")
            scheduler = build_scheduler()
            scheduler.start()
            try:
                await publish_tick()
            except Exception:
                log.exception("Scheduler bootstrap tick failed; retrying on next interval")
        try:
            yield
        finally:
            if scheduler is not None:
                scheduler.shutdown(wait=False)

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
        allow_headers=["Content-Type", "X-Requested-With", settings.csrf_header_name, "X-Request-ID", "X-Correlation-ID"],
        expose_headers=["X-Request-ID", "X-Correlation-ID"],
    )
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        started = time.monotonic()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        correlation_id = request.headers.get("X-Correlation-ID") or request_id
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        tokens = bind_request_context(request_id, correlation_id)
        try:
            response = await call_next(request)
        finally:
            reset_request_context(tokens)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            DOCS_CONTENT_SECURITY_POLICY if request.url.path in DOCS_PATHS else API_CONTENT_SECURITY_POLICY
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
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
        status_code, body = await readiness_payload(probe_storage)
        return JSONResponse(status_code=status_code, content=body)

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
    """Consume RabbitMQ jobs outside the API process.

    For ~20-user deployments keep a single worker container with low
    ``WORKER_PREFETCH``. HTTP handlers must only publish; never run Drive
    sync, exports, scans, or notification delivery inline.
    """
    prefetch = max(1, int(settings.worker_prefetch))
    # Prefer explicit concurrency when set; never exceed prefetch.
    qos = max(1, min(prefetch, int(settings.worker_concurrency) or prefetch))
    poll_seconds = max(0.5, float(settings.worker_outbox_poll_seconds))
    log.info("Worker starting (prefetch=%s qos=%s poll=%ss)", prefetch, qos, poll_seconds)
    while True:
        try:
            connection = await aio_pika.connect_robust(settings.rabbitmq_url)
            async with connection:
                channel = await connection.channel(publisher_confirms=True)
                await channel.set_qos(prefetch_count=qos)
                await _consume(channel)
                while True:
                    await publish_outbox(channel)
                    await complete_exports()
                    await asyncio.sleep(poll_seconds)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Worker connection failed; retrying")
            await asyncio.sleep(5)


async def run_telegram_service() -> None:
    """Dedicated Telegram bot process (long polling). Kept out of the worker so
    bot traffic never competes with job consumption."""
    from app.jobs.telegram_bot import run_telegram_bot

    log.info("Telegram service starting (polling=%s)", settings.telegram_bot_polling)
    await run_telegram_bot()


def build_scheduler() -> AsyncIOScheduler:
    """Construct the APScheduler instance with reconcile/reminder/cleanup jobs.

    Jobs only publish durable messages for workers — they never perform side
    effects inline. Reused by the standalone scheduler process and, when
    ``SCHEDULER_IN_API=true``, by the API process for small deployments.
    """
    if (settings.scheduler_engine or "apscheduler").lower() != "apscheduler":
        raise RuntimeError(f"Unsupported SCHEDULER_ENGINE={settings.scheduler_engine!r}; use apscheduler")

    coalesce = bool(settings.scheduler_coalesce)
    max_instances = max(1, int(settings.scheduler_max_instances_per_job))
    misfire = max(0, int(settings.scheduler_misfire_grace_seconds))
    job_defaults = {
        "coalesce": coalesce,
        "max_instances": max_instances,
        "misfire_grace_time": misfire,
    }
    scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone, job_defaults=job_defaults)
    scheduler.add_job(
        reconcile,
        "interval",
        minutes=max(1, int(settings.scheduler_reconcile_interval_minutes)),
        id="reconcile",
        coalesce=coalesce,
        max_instances=max_instances,
        misfire_grace_time=misfire,
    )
    scheduler.add_job(
        due_meeting_reminders,
        "interval",
        minutes=max(1, int(settings.scheduler_meeting_reminder_interval_minutes)),
        id="meeting-reminders",
        coalesce=coalesce,
        max_instances=max_instances,
        misfire_grace_time=misfire,
    )
    scheduler.add_job(
        cleanup_expired_exports,
        "interval",
        hours=max(1, int(settings.scheduler_export_cleanup_interval_hours)),
        id="export-cleanup",
        coalesce=coalesce,
        max_instances=max_instances,
        misfire_grace_time=misfire,
    )
    log.info(
        "Scheduler configured (tz=%s reconcile=%sm reminders=%sm cleanup=%sh)",
        settings.scheduler_timezone,
        settings.scheduler_reconcile_interval_minutes,
        settings.scheduler_meeting_reminder_interval_minutes,
        settings.scheduler_export_cleanup_interval_hours,
    )
    return scheduler


async def run_scheduler() -> None:
    """Standalone scheduler process: APScheduler ticks only.

    Due work is published to RabbitMQ for workers. Prefer this process in
    multi-worker or multi-instance deployments; use ``SCHEDULER_IN_API=true``
    only for small single-process deployments (it runs inside the API process).
    """
    scheduler = build_scheduler()
    scheduler.start()
    await publish_tick()
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        scheduler.shutdown(wait=False)
        await close_connection()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="app.main", description="Docetra API / worker / scheduler / telegram")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=("api", "worker", "scheduler", "telegram"),
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
    if args.mode == "telegram":
        asyncio.run(run_telegram_service())
        return
    # api mode without uvicorn is uncommon; print guidance
    print("API mode: run with uvicorn, e.g. uvicorn app.main:app --host 0.0.0.0 --port 8000", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
