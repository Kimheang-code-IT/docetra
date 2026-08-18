import uuid
import time
import logging
from contextlib import asynccontextmanager
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
from app.core.permissions import ALL_PERMISSIONS
from app.core.security import hash_password
from app.db import SessionLocal, User
from app.modules.identity import ensure_admin_entity
from app.core.metrics import observe, prometheus_response

log = logging.getLogger(__name__)

async def seed_admin():
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(User.email == settings.admin_email.lower()))
        if not user:
            user = User(
                email=settings.admin_email.lower(),
                name=settings.admin_name,
                password_hash=hash_password(settings.admin_password),
                role="SuperAdmin",
                permissions=ALL_PERMISSIONS,
            )
            db.add(user)
            await db.flush()
        elif not user.permissions:
            user.permissions = ALL_PERMISSIONS
        await ensure_admin_entity(db, user)
        await db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_production()
    try:
        await seed_admin()
    except Exception:
        # Alembic may still be applying on a sibling container.
        pass
    yield

app = FastAPI(title="Docetra API", version=__version__, openapi_url="/api/v2/openapi.json", docs_url="/api/v2/docs", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Requested-With", settings.csrf_header_name],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

@app.middleware("http")
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

@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID") or str(uuid.uuid4())
    message = str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": message, "error": {"code": f"HTTP_{exc.status_code}", "message": message, "fields": {}, "requestId": request_id}},
        headers={"X-Request-ID": request_id, **(exc.headers or {})},
    )

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    fields = [{"field": ".".join(map(str, item["loc"])), "message": item["msg"]} for item in exc.errors()]
    return JSONResponse(status_code=422, content={"message": "Validation failed", "error": {"code": "VALIDATION_ERROR", "message": "Validation failed", "fields": fields, "requestId": request_id}})

@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", None) or str(uuid.uuid4())
    log.exception("Unhandled request error request_id=%s", request_id, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "error": {"code": "INTERNAL_ERROR", "message": "Internal server error", "fields": {}, "requestId": request_id}},
        headers={"X-Request-ID": request_id},
    )

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": __version__}

@app.get("/ready", tags=["health"])
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

@app.get("/metrics", include_in_schema=False)
async def metrics():
    return await prometheus_response()

app.include_router(api_router)
