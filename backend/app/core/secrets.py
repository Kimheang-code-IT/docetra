import base64
import hashlib
import os
from copy import deepcopy

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings

PREFIX = "enc:v1:"
MASK = "••••••"
SENSITIVE_KEYS = {"password", "secret", "secretkey", "accesskey", "clientsecret", "bottoken", "token", "chatid"}


def _cipher() -> AESGCM:
    key = hashlib.sha256(("docetra:settings:" + (settings.settings_encryption_key or settings.session_secret)).encode()).digest()
    return AESGCM(key)


def encrypt_value(value: str) -> str:
    if not value or value.startswith(PREFIX):
        return value
    nonce = os.urandom(12)
    encrypted = _cipher().encrypt(nonce, value.encode(), b"docetra-settings-v1")
    return PREFIX + base64.urlsafe_b64encode(nonce + encrypted).decode()


def decrypt_value(value: str) -> str:
    if not value.startswith(PREFIX):
        return value
    raw = base64.urlsafe_b64decode(value[len(PREFIX):])
    return _cipher().decrypt(raw[:12], raw[12:], b"docetra-settings-v1").decode()


def _walk(value, transform):
    if isinstance(value, dict):
        return {key: transform(key, _walk(item, transform)) for key, item in value.items()}
    if isinstance(value, list):
        return [_walk(item, transform) for item in value]
    return value


def protect_mapping(value: dict) -> dict:
    source = deepcopy(value)
    return _walk(source, lambda key, item: encrypt_value(item) if key.lower() in SENSITIVE_KEYS and isinstance(item, str) else item)


def reveal_mapping(value: dict) -> dict:
    source = deepcopy(value)
    return _walk(source, lambda key, item: decrypt_value(item) if key.lower() in SENSITIVE_KEYS and isinstance(item, str) else item)


def mask_mapping(value: dict) -> dict:
    source = reveal_mapping(value)
    return _walk(source, lambda key, item: MASK if key.lower() in SENSITIVE_KEYS and isinstance(item, str) and item else item)
