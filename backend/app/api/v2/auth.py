import base64
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import (
    current_user,
    delete_session,
    hash_password,
    issue_session,
    public_user,
    redis,
    refresh_session,
    revoke_user_tokens,
    verify_password,
)
from app.core.secrets import encrypt_value
from app.core.rate_limit import (
    clear_login_failures,
    enforce_rate_limit,
    ensure_not_locked,
    record_login_failure,
    safe_key,
)
from app.db import Entity, Outbox, User, get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class Login(BaseModel):
    email: str
    password: str


class EmailBody(BaseModel):
    email: str


@router.post("/login")
async def login(body: Login, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    email = body.email.strip().lower()
    client = request.client.host if request.client else "unknown"
    await enforce_rate_limit(f"rate:login:{client}:{safe_key(email)}", limit=settings.login_rate_limit, window_seconds=settings.login_rate_window_seconds)
    await ensure_not_locked(email)
    user = await db.scalar(select(User).where(User.email == email))
    if not user or not user.active or not verify_password(body.password, user.password_hash):
        await record_login_failure(email)
        raise HTTPException(401, "Invalid email or password")
    await clear_login_failures(email)
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await issue_session(response, user)
    return {"data": {"user": public_user(user)}}


@router.get("/me")
async def me(user: User = Depends(current_user)):
    return {"data": public_user(user)}


@router.post("/refresh")
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    user = await refresh_session(request, response, db)
    return {"data": {"user": public_user(user)}}


@router.post("/logout")
async def logout(request: Request, response: Response):
    await delete_session(
        response,
        request.cookies.get(settings.session_cookie_name),
        request.cookies.get(settings.refresh_cookie_name),
    )
    return {"data": {"loggedOut": True}}


def reset_digest(email: str, code: str) -> str:
    return hmac.new(settings.password_reset_secret.encode(), f"{email}:{code}".encode(), hashlib.sha256).hexdigest()


@router.post("/forgot-password")
@router.post("/forgot-password/resend")
async def forgot(body: EmailBody, request: Request, db: AsyncSession = Depends(get_db)):
    email = body.email.strip().lower()
    client = request.client.host if request.client else "unknown"
    await enforce_rate_limit(
        f"rate:password-reset:{client}:{safe_key(email)}",
        limit=settings.forgot_password_rate_limit,
        window_seconds=settings.forgot_password_rate_window_seconds,
    )
    user = await db.scalar(select(User).where(User.email == email))
    result = {"sent": True}
    if user:
        code = f"{secrets.randbelow(1_000_000):06d}"
        await redis.setex(f"password-reset:{email}", 15 * 60, reset_digest(email, code))
        db.add(Outbox(topic="notifications.email.security", payload={"kind": "password_reset", "email": email, "code": encrypt_value(code)}))
        await db.commit()
        if settings.app_env == "development":
            result["debugCode"] = code
    return {"data": result}


@router.post("/forgot-password/verify")
async def verify_reset(body: dict):
    email = str(body.get("email") or "").strip().lower()
    code = str(body.get("code") or "")
    expected = await redis.get(f"password-reset:{email}")
    if not expected or not hmac.compare_digest(expected, reset_digest(email, code)):
        raise HTTPException(400, "Invalid code")
    return {"data": {"verified": True}}


@router.post("/forgot-password/reset")
async def reset_password(body: dict, db: AsyncSession = Depends(get_db)):
    email = str(body.get("email") or "").strip().lower()
    code = str(body.get("code") or "")
    expected = await redis.get(f"password-reset:{email}")
    password = str(body.get("password") or "")
    if (
        not expected
        or not hmac.compare_digest(expected, reset_digest(email, code))
        or password != str(body.get("passwordConfirmation") or "")
        or len(password) < settings.minimum_password_length
    ):
        raise HTTPException(422, "Invalid reset request")
    user = await db.scalar(select(User).where(User.email == email))
    if user:
        user.password_hash = hash_password(password)
        db.add(Entity(resource="system-logs", payload={"level": "info", "action": "security.password_reset", "userId": str(user.id), "occurredAt": datetime.now(timezone.utc).isoformat()}, status="active", created_by=user.id, updated_by=user.id))
        await db.commit()
        await redis.delete(f"password-reset:{email}")
        await revoke_user_tokens(str(user.id))
    return {"data": {"reset": True}}


@router.post("/change-password")
async def change_password(
    body: dict,
    request: Request,
    response: Response,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(str(body.get("currentPassword") or ""), user.password_hash):
        raise HTTPException(401, "Current password is incorrect")
    password = str(body.get("password") or "")
    if password != str(body.get("passwordConfirmation") or "") or len(password) < settings.minimum_password_length:
        raise HTTPException(422, "Passwords do not match or are too short")
    user.password_hash = hash_password(password)
    await db.commit()
    await revoke_user_tokens(str(user.id))
    await issue_session(response, user)
    return {"data": {"changed": True}}


@router.put("/profile/avatar")
async def avatar(body: dict, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    value = str(body.get("avatar") or "")
    match = re.match(r"^data:image/(png|jpeg|webp|gif);base64,(.+)$", value, re.I)
    if not match:
        raise HTTPException(422, "Avatar must be a PNG, JPEG, WebP, or GIF data URL")
    try:
        raw = base64.b64decode(match.group(2), validate=True)
    except Exception as exc:
        raise HTTPException(422, "Invalid avatar data") from exc
    if len(raw) > 2 * 1024 * 1024:
        raise HTTPException(413, "Avatar exceeds 2 MB")
    user.avatar = value
    await db.commit()
    return {"data": {"avatar": value}}


@router.delete("/profile/avatar")
async def remove_avatar(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    user.avatar = None
    await db.commit()
    return {"data": {"removed": True}}
