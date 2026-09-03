import asyncio
import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import settings

log = logging.getLogger(__name__)


def _deliver_smtp(*, host: str, port: int, username: str, password: str, use_tls: bool, message: EmailMessage, timeout: int = 15) -> None:
    with smtplib.SMTP(host, port, timeout=timeout) as client:
        if use_tls:
            client.starttls()
        if username:
            client.login(username, password)
        client.send_message(message)


async def send_password_reset(to_email: str, code: str, *, smtp: dict) -> dict:
    body = (
        f"Your Docetra password reset code is {code}.\n"
        f"It expires in 15 minutes.\n"
        f"Reset page: {settings.password_reset_url}"
    )
    if not smtp["enabled"] or not smtp["smtpHost"]:
        log.info("Password reset for %s (SMTP unconfigured): code omitted outside development", to_email)
        return {"status": "disabled"}
    message = EmailMessage()
    message["Subject"] = "Docetra password reset"
    from_addr = smtp["fromEmail"] or settings.email_from_address
    message["From"] = formataddr((smtp["fromName"], from_addr)) if from_addr else smtp["fromName"]
    message["To"] = to_email
    message.set_content(body)
    try:
        await asyncio.to_thread(
            _deliver_smtp,
            host=smtp["smtpHost"],
            port=smtp["smtpPort"],
            username=smtp["username"],
            password=smtp["password"],
            use_tls=smtp["useTls"],
            message=message,
            timeout=smtp["timeoutSeconds"],
        )
        return {"status": "sent"}
    except (OSError, smtplib.SMTPException):
        log.exception("Failed to send password reset email to %s", to_email)
        raise


async def send_test_email(to_email: str, *, smtp: dict | None = None) -> dict:
    if smtp is not None:
        encryption = str(smtp.get("encryption") or "starttls").lower()
        cfg = {
            "enabled": True,
            "smtpHost": str(smtp.get("smtpHost") or settings.smtp_host or ""),
            "smtpPort": int(smtp.get("smtpPort") or settings.smtp_port or 587),
            "username": str(smtp.get("username") or settings.smtp_username or ""),
            "password": str(smtp.get("password") or settings.smtp_password or ""),
            "useTls": encryption in {"starttls", "tls", "ssl"} if smtp.get("encryption") is not None else (
                settings.smtp_use_tls if smtp.get("useTls") is None else bool(smtp.get("useTls"))
            ),
            "fromName": str(smtp.get("fromName") or "Docetra"),
            "fromEmail": str(smtp.get("fromEmail") or settings.email_from_address or ""),
            "timeoutSeconds": int(smtp.get("timeoutSeconds") or 10),
        }
    else:
        cfg = {
            "enabled": bool(settings.smtp_host),
            "smtpHost": settings.smtp_host or "",
            "smtpPort": settings.smtp_port or 587,
            "username": settings.smtp_username or "",
            "password": settings.smtp_password or "",
            "useTls": settings.smtp_use_tls,
            "fromName": "Docetra",
            "fromEmail": settings.email_from_address or "",
            "timeoutSeconds": 10,
        }
    host = cfg["smtpHost"]
    if not host:
        return {"status": "disabled", "message": "SMTP is not configured"}
    message = EmailMessage()
    message["Subject"] = "Docetra test email"
    from_addr = cfg["fromEmail"] or settings.email_from_address
    message["From"] = formataddr((cfg["fromName"], from_addr)) if from_addr else cfg["fromName"]
    message["To"] = to_email
    message.set_content("Docetra email connection test.")
    await asyncio.to_thread(
        _deliver_smtp,
        host=host,
        port=cfg["smtpPort"],
        username=cfg["username"],
        password=cfg["password"],
        use_tls=cfg["useTls"],
        message=message,
        timeout=cfg["timeoutSeconds"],
    )
    return {"status": "connected", "message": "Test email sent"}
