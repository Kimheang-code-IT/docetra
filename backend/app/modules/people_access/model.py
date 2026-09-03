"""People Access-owned canonical SQLAlchemy models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import ActiveFlagMixin, OfficerActorMixin, StatusMixin, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class User(UUIDPrimaryKeyMixin, StatusMixin, VersionMixin, TimestampMixin, Base):
    """Local auth account (password_hash retained; draft Supabase-only columns omitted)."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(80), default="User")
    officer_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    avatar: Mapped[str | None] = mapped_column(Text)
    permissions: Mapped[list] = mapped_column(JSONB, default=list)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    role_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    phone: Mapped[str | None] = mapped_column(String(40))
    app_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    user_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)


class Officer(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, ActiveFlagMixin, Base):
    __tablename__ = "officer"

    nam: Mapped[str] = mapped_column(String(200), default="")
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id", ondelete="SET NULL"))
    role_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("role.id", ondelete="SET NULL"))
    auth_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), unique=True)
    profile_url: Mapped[str | None] = mapped_column(String(500))
    email: Mapped[str | None] = mapped_column(String(320))


class OfficerIdentifier(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, Base):
    __tablename__ = "officer_identifier"

    officer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("officer.id", ondelete="CASCADE"), index=True)
    identifier_type: Mapped[str] = mapped_column(Text)
    identifier: Mapped[str] = mapped_column(Text)
    key1: Mapped[str | None] = mapped_column(Text)


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
    scope: Mapped[str] = mapped_column(String(20), default="all", server_default="all")
