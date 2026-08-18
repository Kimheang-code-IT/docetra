import logging
import smtplib
import asyncio
from email.message import EmailMessage
from app.core.config import settings

log = logging.getLogger(__name__)


async def send_password_reset(to_email: str, code: str) -> dict:
    body = (
        f"Your Docetra password reset code is {code}.\n"
        f"It expires in 15 minutes.\n"
        f"Reset page: {settings.password_reset_url}"
    )
    if not settings.smtp_host:
        log.info("Password reset for %s (SMTP unconfigured): code omitted outside development", to_email)
        return {"status": "disabled"}
    message = EmailMessage()
    message["Subject"] = "Docetra password reset"
    message["From"] = settings.email_from_address
    message["To"] = to_email
    message.set_content(body)
    try:
        def deliver():
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                if settings.smtp_username:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)

        await asyncio.to_thread(deliver)
        return {"status": "sent"}
    except (OSError, smtplib.SMTPException):
        log.exception("Failed to send password reset email to %s", to_email)
        raise


async def send_test_email(to_email: str, *, smtp: dict | None = None) -> dict:
    cfg = smtp or {}
    host = str(cfg.get("smtpHost") or settings.smtp_host)
    if not host:
        return {"status": "disabled", "message": "SMTP is not configured"}
    message = EmailMessage()
    message["Subject"] = "Docetra test email"
    message["From"] = settings.email_from_address
    message["To"] = to_email
    message.set_content("Docetra email connection test.")
    port = int(cfg.get("smtpPort") or settings.smtp_port)
    username = str(cfg.get("username") or settings.smtp_username)
    password = str(cfg.get("password") or settings.smtp_password)
    use_tls = settings.smtp_use_tls if cfg.get("useTls") is None else bool(cfg.get("useTls"))

    def deliver():
        with smtplib.SMTP(host, port, timeout=15) as client:
            if use_tls:
                client.starttls()
            if username:
                client.login(username, password)
            client.send_message(message)

    await asyncio.to_thread(deliver)
    return {"status": "connected", "message": "Test email sent"}
