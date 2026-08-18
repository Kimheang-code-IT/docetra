import json
import secrets
import uuid
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Request, Response
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.jwt import decode_token, encode_token
from app.db import User, get_db

passwords = CryptContext(schemes=["bcrypt"], deprecated="auto")
redis = Redis.from_url(settings.redis_url, decode_responses=True)

CSRF_EXEMPT_PATHS = {
    "/api/v2/auth/login",
    "/api/v2/auth/forgot-password",
    "/api/v2/auth/forgot-password/verify",
    "/api/v2/auth/forgot-password/resend",
    "/api/v2/auth/forgot-password/reset",
}


def hash_password(value: str) -> str:
    return passwords.hash(value)


def verify_password(value: str, hashed: str) -> bool:
    return passwords.verify(value, hashed)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _cookie_kwargs(*, httponly: bool, max_age: int) -> dict:
    return {
        "max_age": max_age,
        "httponly": httponly,
        "secure": settings.session_cookie_secure,
        "samesite": settings.session_cookie_samesite,
        "path": "/",
    }


async def _store_token(jti: str, user_id: str, csrf: str, ttl: int, token_type: str) -> None:
    await redis.setex(f"jwt:{jti}", ttl, json.dumps({"userId": user_id, "csrf": csrf, "typ": token_type}))
    await redis.sadd(f"user-tokens:{user_id}", jti)
    await redis.expire(f"user-tokens:{user_id}", max(ttl, settings.jwt_refresh_days * 86400))


async def _revoke_jti(jti: str, user_id: str | None = None) -> None:
    raw = await redis.get(f"jwt:{jti}")
    await redis.delete(f"jwt:{jti}")
    if not user_id and raw:
        try:
            user_id = json.loads(raw).get("userId")
        except (ValueError, TypeError):
            user_id = None
    if user_id:
        await redis.srem(f"user-tokens:{user_id}", jti)


async def revoke_user_tokens(user_id: str) -> None:
    jtis = await redis.smembers(f"user-tokens:{user_id}")
    if jtis:
        await redis.delete(*(f"jwt:{jti}" for jti in jtis))
    await redis.delete(f"user-tokens:{user_id}")


async def issue_session(response: Response, user: User) -> str:
    access, access_jti, _ = encode_token(subject=str(user.id), token_type="access", minutes=settings.jwt_access_minutes)
    refresh, refresh_jti, _ = encode_token(subject=str(user.id), token_type="refresh", days=settings.jwt_refresh_days)
    csrf = secrets.token_urlsafe(24)
    access_ttl = settings.jwt_access_minutes * 60
    refresh_ttl = settings.jwt_refresh_days * 86400
    await _store_token(access_jti, str(user.id), csrf, access_ttl, "access")
    await _store_token(refresh_jti, str(user.id), csrf, refresh_ttl, "refresh")
    response.set_cookie(settings.session_cookie_name, access, **_cookie_kwargs(httponly=True, max_age=access_ttl))
    response.set_cookie(settings.refresh_cookie_name, refresh, **_cookie_kwargs(httponly=True, max_age=refresh_ttl))
    response.set_cookie(settings.csrf_cookie_name, csrf, **_cookie_kwargs(httponly=False, max_age=access_ttl))
    return access_jti


create_session = issue_session


async def delete_session(response: Response, access_token: str | None, refresh_token: str | None = None) -> None:
    for token in (access_token, refresh_token):
        if not token:
            continue
        try:
            payload = decode_token(token, verify_exp=False)
        except InvalidTokenError:
            continue
        await _revoke_jti(str(payload.get("jti") or ""), str(payload.get("sub") or "") or None)
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.refresh_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")


async def _user_from_token(db: AsyncSession, token: str, *, token_type: str, verify_exp: bool) -> tuple[User, dict, dict]:
    try:
        payload = decode_token(token, verify_exp=verify_exp)
    except ExpiredSignatureError as exc:
        raise HTTPException(401, {"code": "token_expired", "message": "Session expired"}) from exc
    except InvalidTokenError as exc:
        raise HTTPException(401, "Authentication required") from exc
    if payload.get("typ") != token_type:
        raise HTTPException(401, "Authentication required")
    jti = str(payload.get("jti") or "")
    stored = await redis.get(f"jwt:{jti}")
    if not stored:
        raise HTTPException(401, {"code": "token_expired", "message": "Session expired"})
    try:
        session = json.loads(stored)
    except (ValueError, TypeError) as exc:
        raise HTTPException(401, "Invalid session") from exc
    try:
        uid = uuid.UUID(str(payload.get("sub") or session.get("userId")))
    except ValueError as exc:
        raise HTTPException(401, "Invalid session") from exc
    user = await db.scalar(select(User).where(User.id == uid, User.active.is_(True)))
    if not user:
        raise HTTPException(401, "Account is unavailable")
    return user, payload, session


async def current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise HTTPException(401, "Authentication required")
    user, _payload, _session = await _user_from_token(db, token, token_type="access", verify_exp=True)
    return user


async def refresh_session(request: Request, response: Response, db: AsyncSession) -> User:
    refresh = request.cookies.get(settings.refresh_cookie_name)
    if not refresh:
        raise HTTPException(401, {"code": "token_expired", "message": "Session expired"})
    user, payload, _session = await _user_from_token(db, refresh, token_type="refresh", verify_exp=True)
    await _revoke_jti(str(payload.get("jti") or ""), str(user.id))
    await issue_session(response, user)
    return user


async def csrf_protect(request: Request):
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    if request.url.path in CSRF_EXEMPT_PATHS:
        return
    cookie = request.cookies.get(settings.csrf_cookie_name)
    header = request.headers.get(settings.csrf_header_name)
    if not cookie or not header or not secrets.compare_digest(cookie, header):
        raise HTTPException(403, "CSRF validation failed")
    if request.url.path == "/api/v2/auth/refresh":
        return
    access = request.cookies.get(settings.session_cookie_name)
    if not access:
        raise HTTPException(403, "CSRF session binding failed")
    try:
        payload = decode_token(access, verify_exp=False)
        stored = await redis.get(f"jwt:{payload.get('jti')}")
        expected = json.loads(stored)["csrf"] if stored else ""
    except (InvalidTokenError, ValueError, KeyError, TypeError):
        expected = ""
    if not expected or not secrets.compare_digest(cookie, expected):
        raise HTTPException(403, "CSRF session binding failed")


def person(user: User | None):
    return None if not user else {"id": str(user.id), "name": user.name, "email": user.email, "avatarUrl": user.avatar}


def public_user(user: User):
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "avatar": user.avatar,
        "permissions": user.permissions or [],
        "pageAccess": ["ALL_PAGES"] if user.role in {"SuperAdmin", "Admin"} else [],
    }


current_user = current_user
public_user = public_user
