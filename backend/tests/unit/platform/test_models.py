"""Platform model contracts — outbox and audit column defaults."""

from app.platform.audit.model import AuditLog, NotificationAuditLog
from app.platform.messaging.model import Outbox


def test_outbox_columns_and_defaults():
    table = Outbox.__table__
    assert table.c.topic.type.length == 160
    assert table.c.attempts.default.arg == 0
    assert table.c.processed_at.nullable is True
    assert table.c.processed_at.default is None


def test_audit_log_append_only_columns():
    table = AuditLog.__table__
    assert table.c.status_code.default.arg == "success"
    assert table.c.source_log.default.arg == "unknown"
    assert table.c.detail_data.default is not None
    assert table.c.action_code.type.length == 120
    assert table.c.row_id.index is True
    assert table.c.created_at.nullable is False


def test_notification_audit_default_unprocessed():
    table = NotificationAuditLog.__table__
    assert table.c.processed.default.arg is False
    assert table.c.log_id.nullable is True
