"""admin_config — runtime defaults and secret-preserving merge."""

from app.core.config import settings
from app.core.secrets import MASK
import app.modules.admin_config.services.runtime as runtime
from app.modules.admin_config.services.settings import DEFAULT_APP_CONFIG, merge_setting


def test_email_smtp_prefers_app_config_over_env():
    config = {
        "email": {
            "enabled": True,
            "smtpHost": "smtp.example.com",
            "smtpPort": 465,
            "username": "mailer",
            "password": "secret",
            "encryption": "ssl",
            "fromName": "Docetra Mail",
            "fromEmail": "noreply@example.com",
        }
    }
    smtp = runtime.email_smtp(config)
    assert smtp["enabled"] is True
    assert smtp["smtpHost"] == "smtp.example.com"
    assert smtp["smtpPort"] == 465
    assert smtp["password"] == "secret"
    assert smtp["useTls"] is True


def test_email_smtp_falls_back_to_env_when_app_config_incomplete(monkeypatch):
    monkeypatch.setattr(settings, "smtp_host", "env.smtp.local")
    monkeypatch.setattr(settings, "smtp_port", 2525)
    monkeypatch.setattr(settings, "smtp_username", "env-user")
    monkeypatch.setattr(settings, "smtp_password", "env-pass")
    monkeypatch.setattr(settings, "email_from_address", "env@example.com")
    monkeypatch.setattr(settings, "smtp_use_tls", True)

    smtp = runtime.email_smtp({"email": {"enabled": True}})
    assert smtp["smtpHost"] == "env.smtp.local"
    assert smtp["fromEmail"] == "env@example.com"


def test_general_defaults_merge_app_config():
    general = runtime.general_defaults({"general": {"enableComments": False, "defaultPageSize": 50}})
    assert general["enableComments"] is False
    assert general["defaultPageSize"] == 50
    assert "defaultLandingPage" in general


def test_default_app_config_has_required_sections():
    assert "general" in DEFAULT_APP_CONFIG
    assert "email" in DEFAULT_APP_CONFIG
    assert "telegram" in DEFAULT_APP_CONFIG
    assert "security" in DEFAULT_APP_CONFIG


def test_merge_setting_preserves_masked_secrets():
    current = {"email": {"password": "real-secret", "smtpHost": "a"}, "telegram": {"botToken": "tok"}}
    incoming = {"email": {"password": MASK, "smtpHost": "b"}, "telegram": {"botToken": ""}}
    merged = merge_setting(current, incoming)
    assert merged["email"]["password"] == "real-secret"
    assert merged["email"]["smtpHost"] == "b"
    assert merged["telegram"]["botToken"] == "tok"
