from sqlalchemy import DateTime, Integer, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import utcnow
import uuid
from datetime import datetime


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class VersionMixin:
    version: Mapped[int] = mapped_column(Integer, default=1)


class StatusMixin:
    status: Mapped[str] = mapped_column(String(40), default="active")


class OfficerActorMixin:
    """Draft DB: created_by / updated_by store officer.id (soft refs to avoid create-order cycles)."""

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)


class ActiveFlagMixin:
    is_active: Mapped[int] = mapped_column(SmallInteger, default=0)
