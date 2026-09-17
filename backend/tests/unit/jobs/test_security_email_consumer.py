"""Password-reset consumer — Telegram fallback when SMTP is unconfigured."""

import app.jobs.consumers as consumers
from app.modules.admin_config.services import runtime as runtime_module
from tests.unit.support import FakeSession


def _patch_runtime(monkeypatch, *, telegram: dict) -> None:
    async def load_config(_db=None):
        return {}

    monkeypatch.setattr(runtime_module, "load_app_config", load_config)
    monkeypatch.setattr(runtime_module, "email_smtp", lambda _config: {"enabled": False, "smtpHost": ""})
    monkeypatch.setattr(runtime_module, "telegram_meeting", lambda _config: telegram)


async def test_password_reset_delivers_code_via_telegram(monkeypatch):
    sent: list[tuple[str, str, str]] = []

    async def fake_email(_email, _code, *, smtp):
        return {"status": "disabled"}

    async def fake_send(token, chat_id, text):
        sent.append((token, str(chat_id), text))

    _patch_runtime(monkeypatch, telegram={
        "enabled": True,
        "botToken": "TOKEN",
        "destinations": [{"chatId": "1489002750", "enabled": True}, {"chatId": "999", "enabled": False}],
    })
    monkeypatch.setattr(consumers, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(consumers, "decrypt_value", lambda value: value)
    monkeypatch.setattr("app.integrations.email.send_password_reset", fake_email)
    monkeypatch.setattr("app.integrations.telegram.send_message", fake_send)

    await consumers.handle_security_email({"kind": "password_reset", "email": "user@example.com", "code": "123456"})

    assert len(sent) == 1
    assert sent[0][0] == "TOKEN"
    assert sent[0][1] == "1489002750"
    assert "123456" in sent[0][2]
    assert "user@example.com" in sent[0][2]


async def test_password_reset_skips_telegram_when_disabled(monkeypatch):
    sent: list[str] = []

    async def fake_email(_email, _code, *, smtp):
        return {"status": "disabled"}

    async def fake_send(_token, chat_id, _text):
        sent.append(str(chat_id))

    _patch_runtime(monkeypatch, telegram={"enabled": False, "botToken": "TOKEN", "destinations": [{"chatId": "1", "enabled": True}]})
    monkeypatch.setattr(consumers, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(consumers, "decrypt_value", lambda value: value)
    monkeypatch.setattr("app.integrations.email.send_password_reset", fake_email)
    monkeypatch.setattr("app.integrations.telegram.send_message", fake_send)

    await consumers.handle_security_email({"kind": "password_reset", "email": "user@example.com", "code": "123456"})

    assert sent == []


async def test_password_reset_email_failure_still_reaches_telegram(monkeypatch):
    sent: list[str] = []

    async def failing_email(_email, _code, *, smtp):
        raise OSError("smtp down")

    async def fake_send(_token, chat_id, _text):
        sent.append(str(chat_id))

    _patch_runtime(monkeypatch, telegram={"enabled": True, "botToken": "TOKEN", "destinations": [{"chatId": "1", "enabled": True}]})
    monkeypatch.setattr(consumers, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(consumers, "decrypt_value", lambda value: value)
    monkeypatch.setattr("app.integrations.email.send_password_reset", failing_email)
    monkeypatch.setattr("app.integrations.telegram.send_message", fake_send)

    await consumers.handle_security_email({"kind": "password_reset", "email": "user@example.com", "code": "123456"})

    assert sent == ["1"]


async def test_password_reset_skips_group_destinations(monkeypatch):
    sent: list[str] = []

    async def fake_email(_email, _code, *, smtp):
        return {"status": "disabled"}

    async def fake_send(_token, chat_id, _text):
        sent.append(str(chat_id))

    _patch_runtime(monkeypatch, telegram={
        "enabled": True,
        "botToken": "TOKEN",
        "destinations": [
            {"chatId": "1489002750", "enabled": True},
            {"chatId": "-5072227274", "enabled": True},
        ],
    })
    monkeypatch.setattr(consumers, "SessionLocal", lambda: FakeSession())
    monkeypatch.setattr(consumers, "decrypt_value", lambda value: value)
    monkeypatch.setattr("app.integrations.email.send_password_reset", fake_email)
    monkeypatch.setattr("app.integrations.telegram.send_message", fake_send)

    await consumers.handle_security_email({"kind": "password_reset", "email": "user@example.com", "code": "123456"})

    assert sent == ["1489002750"]  # private only, group never receives reset codes
