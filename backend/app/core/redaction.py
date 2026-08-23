from __future__ import annotations

SECRET_KEYS = {
    "password",
    "passwordConfirmation",
    "passwordHash",
    "password_hash",
    "currentPassword",
    "token",
    "secret",
    "secretKey",
    "secret_key",
    "accessKey",
    "access_key",
    "clientSecret",
    "client_secret",
    "botToken",
    "bot_token",
    "authorization",
    "cookie",
    "apiKey",
    "api_key",
    "privateKey",
    "private_key",
    "session",
}

_EXACT = {key.lower() for key in SECRET_KEYS}
_FRAGMENTS = ("password", "secret", "token", "authorization", "cookie", "apikey")
REDACTED = "[REDACTED]"


def is_secret_key(key: str) -> bool:
    lowered = str(key).replace("-", "_").lower()
    if lowered in _EXACT:
        return True
    compact = lowered.replace("_", "")
    return any(fragment in compact for fragment in _FRAGMENTS)


def redact(value):
    if isinstance(value, dict):
        return {key: (REDACTED if is_secret_key(str(key)) else redact(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact(item) for item in value)
    return value


def strip_secrets(payload: dict) -> dict:
    return {key: value for key, value in payload.items() if not is_secret_key(str(key))}
