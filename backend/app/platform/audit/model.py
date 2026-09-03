"""Platform-owned audit trail models (canonical definitions)."""

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Identity, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("officer.id", ondelete="SET NULL"))
    action_code: Mapped[str] = mapped_column(String(120))
    table_name: Mapped[str] = mapped_column(String(120))
    row_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    detail_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[str | None] = mapped_column(Text)
    status_code: Mapped[str] = mapped_column(String(40), default="success")
    source_log: Mapped[str] = mapped_column(String(80), default="unknown")
    raw_text: Mapped[str | None] = mapped_column(Text)
    message: Mapped[str | None] = mapped_column(Text)


class NotificationAuditLog(Base):
    __tablename__ = "notification_audit_log"

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    log_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("audit_log.id", ondelete="SET NULL"))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
