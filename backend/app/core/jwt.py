import uuid
from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import settings


def _secret() -> str:
    return settings.signing_secret


def encode_token(*, subject: str, token_type: str, minutes: int | None = None, days: int | None = None) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    if days is not None:
        expires = now + timedelta(days=days)
    else:
        expires = now + timedelta(minutes=minutes or settings.jwt_access_minutes)
    jti = str(uuid.uuid4())
    payload = {
        "sub": subject,
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "typ": token_type,
    }
    token = jwt.encode(payload, _secret(), algorithm=settings.jwt_algorithm)
    return token, jti, expires


def decode_token(token: str, *, verify_exp: bool = True) -> dict:
    return jwt.decode(
        token,
        _secret(),
        algorithms=[settings.jwt_algorithm],
        options={"verify_exp": verify_exp, "require": ["sub", "jti", "exp", "typ"]},
    )
