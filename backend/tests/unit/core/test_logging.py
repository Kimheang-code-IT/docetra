from app.core.logging import JsonLogFormatter, bind_request_context, reset_request_context
from app.core.redaction import redact, strip_secrets


def test_redact_masks_secret_keys_and_aliases():
    payload = redact({
        "email": "a@b.com",
        "password": "secret-pass",
        "access_key": "minio-key",
        "Authorization": "Bearer abc",
        "nested": {"clientSecret": "hidden", "name": "ok"},
    })
    assert payload["email"] == "a@b.com"
    assert payload["password"] == "[REDACTED]"
    assert payload["access_key"] == "[REDACTED]"
    assert payload["Authorization"] == "[REDACTED]"
    assert payload["nested"]["clientSecret"] == "[REDACTED]"
    assert payload["nested"]["name"] == "ok"


def test_strip_secrets_drops_sensitive_fields():
    cleaned = strip_secrets({"name": "Ada", "passwordHash": "x", "token": "y"})
    assert cleaned == {"name": "Ada"}


def test_json_logs_include_correlation_context_and_redact_extras():
    tokens = bind_request_context("req-1", "corr-9")
    try:
        record = __import__("logging").LogRecord(
            "app.test", 20, __file__, 1, "started", (), None
        )
        record.password = "super-secret"
        line = JsonLogFormatter().format(record)
    finally:
        reset_request_context(tokens)
    assert '"requestId": "req-1"' in line
    assert '"correlationId": "corr-9"' in line
    assert "super-secret" not in line
    assert "[REDACTED]" in line
