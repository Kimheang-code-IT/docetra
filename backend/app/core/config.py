from functools import lru_cache
from typing import Annotated
from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "postgresql://docetra:docetra_local_only@postgres:5432/docetra"
    redis_url: str = "redis://redis:6379/0"
    cache_short_url: str = "redis://redis:6379/1"
    cache_long_url: str = "redis://redis:6379/2"
    rabbitmq_url: str = "amqp://docetra:docetra_rabbit_local_only@rabbitmq:5672/docetra"
    cors_allowed_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]
    trusted_hosts: Annotated[list[str], NoDecode] = ["localhost", "127.0.0.1", "api"]
    session_cookie_name: str = "docetra_session"
    session_cookie_secure: bool = False
    session_cookie_samesite: str = "lax"
    csrf_cookie_name: str = "XSRF-TOKEN"
    csrf_header_name: str = "X-CSRF-Token"
    session_timeout_minutes: int = 480
    session_secret: str = "local-development-change-me"
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_minutes: int = 480
    jwt_refresh_days: int = 7
    refresh_cookie_name: str = "docetra_refresh"
    password_reset_secret: str = "local-reset-change-me"
    settings_encryption_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from_address: str = "no-reply@example.com"
    password_reset_url: str = "http://localhost:3000/auth/reset-password"
    telegram_meeting_bot_enabled: bool = False
    telegram_meeting_bot_token: str = ""
    telegram_devops_bot_enabled: bool = False
    telegram_devops_bot_token: str = ""
    google_drive_access_token: str = ""
    google_drive_folder_id: str = ""
    max_upload_size_mb: int = 25
    allowed_upload_extensions: Annotated[list[str], NoDecode] = ["pdf","doc","docx","xls","xlsx","png","jpg","jpeg","gif","webp","txt","csv"]
    admin_email: str = "admin@gmail.com"
    admin_password: str = "123456"
    admin_name: str = "System Administrator"
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: str = "docetra"
    s3_secret_key: str = "docetra_minio_local_only"
    s3_bucket: str = "docetra"
    s3_use_ssl: bool = False
    scheduler_timezone: str = "UTC"
    meeting_reminder_offsets_minutes: Annotated[list[int], NoDecode] = [1440, 60, 15]
    meeting_recurrence_horizon_days: int = 90
    login_rate_limit: int = 10
    login_rate_window_seconds: int = 60
    max_login_failures: int = 5
    account_lock_minutes: int = 15
    forgot_password_rate_limit: int = 5
    forgot_password_rate_window_seconds: int = 900
    minimum_password_length: int = 8
    job_max_retries: int = 5

    @field_validator("cors_allowed_origins", "trusted_hosts", "allowed_upload_extensions", "meeting_reminder_offsets_minutes", mode="before")
    @classmethod
    def split_csv(cls, value):
        if not isinstance(value, str):
            return value
        parts = [item.strip() for item in value.split(",") if item.strip()]
        if parts and parts[0].lstrip("-").isdigit():
            return [int(item) for item in parts]
        return parts

    @property
    def async_database_url(self):
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    @property
    def signing_secret(self) -> str:
        return self.jwt_secret or self.session_secret

    def validate_production(self) -> None:
        if self.app_env.lower() != "production":
            return
        problems: list[str] = []
        weak = {"", "local-development-change-me", "local-reset-change-me", "123456", "change-me"}
        if self.session_secret in weak or len(self.session_secret) < 32 or "replace" in self.session_secret.lower():
            problems.append("SESSION_SECRET must be unique and at least 32 characters")
        if self.signing_secret in weak or len(self.signing_secret) < 32 or "replace" in self.signing_secret.lower():
            problems.append("JWT_SECRET (or SESSION_SECRET) must be unique and at least 32 characters")
        if self.password_reset_secret in weak or len(self.password_reset_secret) < 32 or "replace" in self.password_reset_secret.lower():
            problems.append("PASSWORD_RESET_SECRET must be unique and at least 32 characters")
        if not self.settings_encryption_key or len(self.settings_encryption_key) < 32 or "replace" in self.settings_encryption_key.lower():
            problems.append("SETTINGS_ENCRYPTION_KEY must be unique and at least 32 characters")
        if not self.session_cookie_secure:
            problems.append("SESSION_COOKIE_SECURE must be true")
        if self.admin_password in weak or len(self.admin_password) < 12 or "replace" in self.admin_password.lower():
            problems.append("ADMIN_PASSWORD must be unique and at least 12 characters")
        if any(origin == "*" or origin.startswith("http://") for origin in self.cors_allowed_origins):
            problems.append("CORS_ALLOWED_ORIGINS must contain only explicit HTTPS origins")
        if "*" in self.trusted_hosts:
            problems.append("TRUSTED_HOSTS must not contain a wildcard")
        if not self.smtp_host:
            problems.append("SMTP_HOST is required so password reset can be delivered")
        elif "replace" in self.smtp_host.lower():
            problems.append("SMTP_HOST must be configured")
        if "docetra_local_only" in self.database_url or "replace" in self.database_url.lower():
            problems.append("DATABASE_URL must use a unique production password")
        if "docetra_rabbit_local_only" in self.rabbitmq_url or "replace" in self.rabbitmq_url.lower():
            problems.append("RABBITMQ_URL must use a unique production password")
        if self.s3_secret_key == "docetra_minio_local_only" or "replace" in self.s3_secret_key.lower():
            problems.append("S3_SECRET_KEY must be configured")
        if problems:
            raise RuntimeError("Invalid production configuration: " + "; ".join(problems))

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
