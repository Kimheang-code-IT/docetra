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
    redis,
    refresh_session,
    revoke_user_tokens,
    verify_password,
)
from app.modules.people_access.dependencies import public_user
from app.core.secrets import encrypt_value
from app.core.http_schemas import AvatarBody, ChangePasswordBody, DataEnvelope, ResetPasswordBody, VerifyResetBody
from app.core.rate_limit import (
    clear_login_failures,
    enforce_rate_limit,
    ensure_not_locked,
    record_login_failure,
    safe_key,
)
from app.db import get_db
from app.platform.messaging.model import Outbox
from app.modules.people_access.model import User
from app.platform.audit.model import AuditLog
from app.modules.admin_config.service import runtime
from app.modules.people_access.services.people import count_users, provision_first_administrator

router = APIRouter(prefix="/auth", tags=["auth"])


class Login(BaseModel):
    email: str
    password: str


class Register(BaseModel):
    name: str
    email: str
    password: str
    passwordConfirmation: str = ""


class EmailBody(BaseModel):
    email: str


async def _security_policy(db: AsyncSession) -> dict:
    return runtime.security_policy(await runtime.load_app_config(db))


@router.get("/bootstrap", response_model=DataEnvelope)
async def bootstrap(db: AsyncSession = Depends(get_db)):
    return {"data": {"needsSetup": await count_users(db) == 0}}


@router.post("/register", response_model=DataEnvelope)
async def register(body: Register, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    email = body.email.strip().lower()
    name = body.name.strip()
    client = request.client.host if request.client else "unknown"
    await enforce_rate_limit(f"rate:register:{client}:{safe_key(email)}", limit=settings.login_rate_limit, window_seconds=settings.login_rate_window_seconds)
    if not name or "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(422, "Name and a valid email are required")
    if body.password != body.passwordConfirmation or len(body.password) < settings.minimum_password_length:
        raise HTTPException(422, "Passwords do not match or are too short")
    user = await provision_first_administrator(db, name=name, email=email, password=body.password)
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    policy = await _security_policy(db)
    _jti, access, refresh = await issue_session(response, user, access_minutes=policy["sessionTimeoutMinutes"])
    return {"data": {"user": public_user(user), "token": access, "refreshToken": refresh}}


@router.post("/login", response_model=DataEnvelope)
async def login(body: Login, request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    email = body.email.strip().lower()
    client = request.client.host if request.client else "unknown"
    await enforce_rate_limit(f"rate:login:{client}:{safe_key(email)}", limit=settings.login_rate_limit, window_seconds=settings.login_rate_window_seconds)
    await ensure_not_locked(email)
    user = await db.scalar(select(User).where(User.email == email))
    if not user or not user.active or not verify_password(body.password, user.password_hash):
        policy = await _security_policy(db)
        await record_login_failure(
            email,
            account_lock_minutes=policy["accountLockMinutes"],
            max_login_attempts=policy["maxLoginAttempts"],
        )
        raise HTTPException(401, "Invalid email or password")
    await clear_login_failures(email)
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    policy = await _security_policy(db)
    _jti, access, refresh = await issue_session(response, user, access_minutes=policy["sessionTimeoutMinutes"])
    return {"data": {"user": public_user(user), "token": access, "refreshToken": refresh}}


@router.get("/me", response_model=DataEnvelope)
async def me(user: User = Depends(current_user)):
    return {"data": public_user(user)}


@router.post("/refresh", response_model=DataEnvelope)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    policy = await _security_policy(db)
    user, access, new_refresh = await refresh_session(
        request,
        response,
        db,
        access_minutes=policy["sessionTimeoutMinutes"],
    )
    return {"data": {**public_user(user), "token": access, "refreshToken": new_refresh}}


@router.post("/logout", response_model=DataEnvelope)
async def logout(request: Request, response: Response):
    await delete_session(
        response,
        request.cookies.get(settings.session_cookie_name),
        request.cookies.get(settings.refresh_cookie_name),
    )
    return {"data": {"loggedOut": True}}


def reset_digest(email: str, code: str) -> str:
    return hmac.new(settings.password_reset_secret.encode(), f"{email}:{code}".encode(), hashlib.sha256).hexdigest()


@router.post("/forgot-password", response_model=DataEnvelope)
@router.post("/forgot-password/resend", response_model=DataEnvelope)
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


@router.post("/forgot-password/verify", response_model=DataEnvelope)
async def verify_reset(body: VerifyResetBody):
    email = body.email.strip().lower()
    code = body.code
    expected = await redis.get(f"password-reset:{email}")
    if not expected or not hmac.compare_digest(expected, reset_digest(email, code)):
        raise HTTPException(400, "Invalid code")
    return {"data": {"verified": True}}


@router.post("/forgot-password/reset", response_model=DataEnvelope)
async def reset_password(body: ResetPasswordBody, db: AsyncSession = Depends(get_db)):
    email = body.email.strip().lower()
    code = body.code
    expected = await redis.get(f"password-reset:{email}")
    password = body.password
    if (
        not expected
        or not hmac.compare_digest(expected, reset_digest(email, code))
        or password != body.passwordConfirmation
        or len(password) < settings.minimum_password_length
    ):
        raise HTTPException(422, "Invalid reset request")
    user = await db.scalar(select(User).where(User.email == email))
    if user:
        user.password_hash = hash_password(password)
        db.add(AuditLog(
            action_code="security.password_reset",
            table_name="users",
            row_id=user.id,
            message="Password reset completed",
            detail_data={"userId": str(user.id), "occurredAt": datetime.now(timezone.utc).isoformat()},
            source_log="system",
            status_code="success",
            created_by=user.officer_id,
        ))
        await db.commit()
        await redis.delete(f"password-reset:{email}")
        await revoke_user_tokens(str(user.id))
    return {"data": {"reset": True}}


@router.post("/change-password", response_model=DataEnvelope)
async def change_password(
    body: ChangePasswordBody,
    response: Response,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.currentPassword, user.password_hash):
        raise HTTPException(401, "Current password is incorrect")
    password = body.password
    if password != body.passwordConfirmation or len(password) < settings.minimum_password_length:
        raise HTTPException(422, "Passwords do not match or are too short")
    user.password_hash = hash_password(password)
    await db.commit()
    await revoke_user_tokens(str(user.id))
    await issue_session(response, user)
    return {"data": {"changed": True}}


@router.put("/profile/avatar", response_model=DataEnvelope)
async def avatar(body: AvatarBody, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    value = body.avatar
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


@router.delete("/profile/avatar", response_model=DataEnvelope)
async def remove_avatar(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    user.avatar = None
    await db.commit()
    return {"data": {"removed": True}}
