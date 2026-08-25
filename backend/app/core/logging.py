from __future__ import annotations

import contextvars
import json
import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.core.redaction import redact

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("correlation_id", default="-")


_RESERVED_RECORD_KEYS = {
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename", "module",
    "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs",
    "relativeCreated", "thread", "threadName", "processName", "process", "message",
    "asctime", "taskName",
}


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "requestId": request_id_var.get(),
            "correlationId": correlation_id_var.get(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        extras = {key: value for key, value in record.__dict__.items() if key not in _RESERVED_RECORD_KEYS}
        if extras:
            payload.update(extras)
        return json.dumps(redact(payload), ensure_ascii=False, default=str)


def bind_request_context(request_id: str, correlation_id: str) -> tuple[contextvars.Token, contextvars.Token]:
    return request_id_var.set(request_id), correlation_id_var.set(correlation_id)


def reset_request_context(tokens: tuple[contextvars.Token, contextvars.Token]) -> None:
    request_id_var.reset(tokens[0])
    correlation_id_var.reset(tokens[1])


def configure_logging() -> None:
    level = logging.DEBUG if settings.app_env.lower() == "development" else logging.INFO
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    # AMQP wire-protocol frame dumps are noise even under DEBUG.
    for name in ("aiormq", "aio_pika"):
        logging.getLogger(name).setLevel(logging.INFO)
