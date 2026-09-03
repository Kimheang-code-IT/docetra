"""Storage Integration-owned canonical SQLAlchemy models."""

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import OfficerActorMixin, TimestampMixin, UUIDPrimaryKeyMixin


class File(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, Base):
    __tablename__ = "file"

    nam: Mapped[str] = mapped_column(String(500), default="")
    path: Mapped[str] = mapped_column(String(1000), default="")
    file_size: Mapped[int] = mapped_column(BigInteger, default=0)
    mime_type: Mapped[str | None] = mapped_column(String(200))
    storage_type: Mapped[str | None] = mapped_column(String(80))
    direct_url: Mapped[str | None] = mapped_column(Text)
    source_table: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(40), default="active")
