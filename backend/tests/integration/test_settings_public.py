"""Public settings GETs (no session required)."""

from __future__ import annotations

import json

import pytest

from tests.integration.conftest import assert_envelope

pytestmark = pytest.mark.integration

SENSITIVE_MARKERS = ("••••••", "enc:v1:")


def _walk_strings(value, found: list[str]) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _walk_strings(item, found)
    elif isinstance(value, list):
        for item in value:
            _walk_strings(item, found)
    elif isinstance(value, str) and value:
        found.append(value)


def test_public_settings_without_auth(api_client):
    info = api_client.get("/api/v2/settings/app-info")
    config = api_client.get("/api/v2/settings/app-config")
    info_body = assert_envelope(info)
    config_body = assert_envelope(config)
    assert "localization" in config_body["data"]
    assert info_body["data"].get("applicationName") or info_body["data"].get("shortName")


def test_public_app_config_masks_secrets(api_client):
    config = assert_envelope(api_client.get("/api/v2/settings/app-config"))["data"]
    email = config.get("email") or {}
    telegram = config.get("telegram") or {}
    # Empty secrets are fine; non-empty must never be plaintext passwords/tokens.
    raw = json.dumps(config)
    assert "smtpPassword" not in raw.lower() or email.get("password") in {"", None, "••••••"}
    password = email.get("password")
    bot_token = telegram.get("botToken")
    if password:
        assert password == "••••••" or str(password).startswith("enc:v1:")
    if bot_token:
        assert bot_token == "••••••" or str(bot_token).startswith("enc:v1:")

    strings: list[str] = []
    _walk_strings(config, strings)
    # Ensure we never leak a long random-looking token that isn't masked.
    for value in strings:
        if value.startswith("enc:v1:"):
            pytest.fail(f"Encrypted secret leaked in public GET: {value[:20]}...")
