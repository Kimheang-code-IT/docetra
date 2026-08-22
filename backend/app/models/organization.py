import uuid

from sqlalchemy import ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import ActiveFlagMixin, OfficerActorMixin, StatusMixin, TimestampMixin, UUIDPrimaryKeyMixin


class OrganizationSector(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, ActiveFlagMixin, Base):
    __tablename__ = "organization_sector"

    nam: Mapped[str] = mapped_column(String(200), default="")
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organization_sector.id", ondelete="SET NULL"))
    description: Mapped[str | None] = mapped_column(Text)


class OrganizationPurpose(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, ActiveFlagMixin, Base):
    __tablename__ = "organization_purpose"

    nam: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str | None] = mapped_column(Text)


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, ActiveFlagMixin, Base):
    __tablename__ = "organization"

    nam: Mapped[str] = mapped_column(String(200), default="")
    lvl: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str | None] = mapped_column(Text)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id", ondelete="SET NULL"))
    sector_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organization_sector.id", ondelete="SET NULL"))
    tax_id: Mapped[str | None] = mapped_column(String(120))
    organization_type: Mapped[str] = mapped_column(String(40), default="government", index=True)
    address: Mapped[str | None] = mapped_column(Text)
    contact_info: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(40))
    organization_purpose_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organization_purpose.id", ondelete="SET NULL"))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    child_ids: Mapped[str | None] = mapped_column(Text)
    code: Mapped[str | None] = mapped_column(String(80))


class LegacyOrganization(UUIDPrimaryKeyMixin, StatusMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    kind: Mapped[str] = mapped_column(String(40), index=True)
    code: Mapped[str | None] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(200))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
