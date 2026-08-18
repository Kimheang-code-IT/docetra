import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.core.permissions import normalize_permission_payload
from app.core.secrets import MASK, mask_mapping, protect_mapping, reveal_mapping
from app.modules.storage_integration.upload_validation import detect_upload_type


def test_secret_mapping_encrypts_reveals_and_masks():
    original = {"email": {"password": "smtp-secret"}, "telegram": {"botToken": "bot-secret"}, "name": "test"}
    protected = protect_mapping(original)
    assert protected["email"]["password"].startswith("enc:v1:")
    assert protected["telegram"]["botToken"].startswith("enc:v1:")
    assert reveal_mapping(protected) == original
    assert mask_mapping(protected)["email"]["password"] == MASK


def test_production_configuration_rejects_development_secrets():
    config = Settings(app_env="production", cors_allowed_origins=["http://localhost:3000"])
    with pytest.raises(RuntimeError, match="Invalid production configuration"):
        config.validate_production()


def test_production_configuration_accepts_hardened_values():
    config = Settings(
        app_env="production",
        session_secret="s" * 48,
        jwt_secret="j" * 48,
        password_reset_secret="r" * 48,
        settings_encryption_key="e" * 48,
        session_cookie_secure=True,
        admin_password="a-unique-admin-password",
        cors_allowed_origins=["https://docetra.example.com"],
        trusted_hosts=["api.docetra.example.com"],
        smtp_host="smtp.example.com",
        database_url="postgresql://docetra:unique-database-password@postgres:5432/docetra",
        rabbitmq_url="amqp://docetra:unique-rabbit-password@rabbitmq:5672/docetra",
        s3_secret_key="unique-object-storage-password",
    )
    config.validate_production()


def test_upload_content_detection_rejects_executable_disguised_as_pdf():
    with pytest.raises(HTTPException) as error:
        detect_upload_type(b"MZ" + b"0" * 30, "pdf")
    assert error.value.status_code == 415


def test_upload_content_detection_accepts_pdf_signature():
    assert detect_upload_type(b"%PDF-1.7\nexample", "pdf") == "application/pdf"


def test_role_permission_payload_rejects_unknown_permission():
    with pytest.raises(ValueError):
        normalize_permission_payload({"permissionRows": [{"type": "department", "permissions": ["view", "launch_missiles"]}]})
