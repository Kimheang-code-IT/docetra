import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow
from app.db.mixins import OfficerActorMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Setting(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, Base):
    __tablename__ = "setting"
    __table_args__ = (UniqueConstraint("key_group", "key", name="uq_setting_group_key"),)

    key_group: Mapped[str] = mapped_column(String(120), index=True)
    key: Mapped[str] = mapped_column(String(160))
    description: Mapped[str | None] = mapped_column(String(500))
    data_type: Mapped[str] = mapped_column(String(40), default="string")
    public_access: Mapped[int] = mapped_column(SmallInteger, default=0)
    visible: Mapped[int] = mapped_column(SmallInteger, default=0)
    ordering: Mapped[int] = mapped_column(Integer, default=0)
    key_value: Mapped[str | None] = mapped_column(Text)


class EnumValue(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, Base):
    __tablename__ = "enum"

    code: Mapped[str] = mapped_column(Text, unique=True)
    value: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str | None] = mapped_column(Text)


class AppSetting(Base):
    """Legacy blob settings — migrated to Setting rows in Phase 5/6."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
