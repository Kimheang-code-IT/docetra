import hashlib

from fastapi import HTTPException

from app.core.security import redis


def safe_key(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()


async def enforce_rate_limit(key: str, *, limit: int, window_seconds: int) -> None:
    value = await redis.incr(key)
    if value == 1:
        await redis.expire(key, window_seconds)
    if value > limit:
        ttl = max(await redis.ttl(key), 1)
        raise HTTPException(429, "Too many requests", headers={"Retry-After": str(ttl)})


async def record_login_failure(email: str) -> None:
    key = f"auth:failure:{safe_key(email)}"
    value = await redis.incr(key)
    await redis.expire(key, settings_account_lock_seconds())
    if value >= settings_max_login_failures():
        await redis.setex(f"auth:locked:{safe_key(email)}", settings_account_lock_seconds(), "1")


async def clear_login_failures(email: str) -> None:
    await redis.delete(f"auth:failure:{safe_key(email)}", f"auth:locked:{safe_key(email)}")


async def ensure_not_locked(email: str) -> None:
    key = f"auth:locked:{safe_key(email)}"
    if await redis.exists(key):
        ttl = max(await redis.ttl(key), 1)
        raise HTTPException(429, "Account temporarily locked", headers={"Retry-After": str(ttl)})


def settings_account_lock_seconds() -> int:
    from app.core.config import settings
    return settings.account_lock_minutes * 60


def settings_max_login_failures() -> int:
    from app.core.config import settings
    return settings.max_login_failures
