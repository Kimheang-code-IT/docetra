import uuid

from sqlalchemy import ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import ActiveFlagMixin, OfficerActorMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Role(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, ActiveFlagMixin, Base):
    __tablename__ = "role"

    nam: Mapped[str] = mapped_column(String(200), default="")
    lvl: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str | None] = mapped_column(Text)


class Menu(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, Base):
    __tablename__ = "menu"

    parent_code: Mapped[str | None] = mapped_column(String(120))
    code: Mapped[str] = mapped_column(String(160), unique=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    icon: Mapped[str | None] = mapped_column(String(120))
    ordering: Mapped[int] = mapped_column(Integer, default=0)
    is_menu: Mapped[int] = mapped_column(SmallInteger, default=1)


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, Base):
    __tablename__ = "permission"
    __table_args__ = (UniqueConstraint("role_id", "code", name="uq_permission_role_code"),)

    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("role.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(160), index=True)
    is_enable: Mapped[int] = mapped_column(SmallInteger, default=0)
