import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import ActiveFlagMixin, OfficerActorMixin, StatusMixin, TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class RecordType(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, ActiveFlagMixin, Base):
    __tablename__ = "record_type"

    code: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    deletable: Mapped[int] = mapped_column(SmallInteger, default=1)
    nam: Mapped[str | None] = mapped_column(String(200))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)


class RecordAttribute(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, Base):
    __tablename__ = "record_attribute"

    code: Mapped[str] = mapped_column(String(120), unique=True)
    data_type: Mapped[str] = mapped_column(String(40), default="string")
    nam: Mapped[str | None] = mapped_column(String(200))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)


class RecordTemplate(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, Base):
    __tablename__ = "record_template"

    record_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("record_type.id", ondelete="CASCADE"), index=True)
    record_attribute_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("record_attribute.id", ondelete="CASCADE"), index=True)
    ordering: Mapped[int] = mapped_column(Integer, default=0)
    is_require: Mapped[int] = mapped_column(SmallInteger, default=0)


class RecordStageTemplate(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, Base):
    __tablename__ = "record_stage_template"

    record_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("record_type.id", ondelete="CASCADE"), index=True)
    ordering: Mapped[int] = mapped_column(Integer, default=0)
    nam: Mapped[str] = mapped_column(String(200), default="")
    is_final: Mapped[int] = mapped_column(SmallInteger, default=0)


class Record(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, VersionMixin, Base):
    __tablename__ = "record"
    __table_args__ = (
        Index("ix_record_type_status_time", "record_type_id", "status", "record_time"),
        Index("ix_record_type_code", "record_type_code"),
    )

    record_type_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("record_type.id", ondelete="SET NULL"), index=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[int] = mapped_column(SmallInteger, default=1)
    record_stage_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("record_stage_template.id", ondelete="SET NULL"))
    record_type_code: Mapped[str | None] = mapped_column(String(120))
    record_content: Mapped[str | None] = mapped_column(Text)
    record_metadata: Mapped[str | None] = mapped_column(Text)
    record_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    record_tag: Mapped[str | None] = mapped_column(Text)
    parent_record: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("record.id", ondelete="SET NULL"))
    record_additional_info: Mapped[str | None] = mapped_column(Text)
    record_flow_code: Mapped[str] = mapped_column(String(80), default="normal")
    stage: Mapped[str | None] = mapped_column(String(100))
    lifecycle: Mapped[str] = mapped_column(String(40), default="active", index=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RecordDetail(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, Base):
    __tablename__ = "record_detail"
    __table_args__ = (Index("ix_record_detail_record_attr", "record_id", "record_attribute_code"),)

    record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("record.id", ondelete="CASCADE"), index=True)
    record_attribute_code: Mapped[str] = mapped_column(String(120), index=True)
    value_number: Mapped[Decimal | None] = mapped_column(Numeric)
    value_string: Mapped[str | None] = mapped_column(Text)
    value_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    value_boolean: Mapped[bool | None] = mapped_column(Boolean)
    value_json: Mapped[dict | None] = mapped_column(JSONB)
    value_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))


class RecordAttachment(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, Base):
    __tablename__ = "record_attachment"

    record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("record.id", ondelete="CASCADE"), index=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("record.id", ondelete="SET NULL"))
    file_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("file.id", ondelete="SET NULL"))


class RecordOrganization(UUIDPrimaryKeyMixin, TimestampMixin, OfficerActorMixin, Base):
    __tablename__ = "record_organization"

    record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("record.id", ondelete="CASCADE"), index=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organization.id", ondelete="CASCADE"), index=True)
    role_type: Mapped[str] = mapped_column(String(40), default="participant")


class Entity(UUIDPrimaryKeyMixin, StatusMixin, VersionMixin, TimestampMixin, Base):
    """Legacy JSONB store — removed in Phase 6 after data migration."""

    __tablename__ = "entities"
    __table_args__ = (Index("ix_entities_resource_status", "resource", "status"),)

    resource: Mapped[str] = mapped_column(String(120), index=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    stage: Mapped[str | None] = mapped_column(String(100))
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    record_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)


class LegacyRecord(UUIDPrimaryKeyMixin, StatusMixin, TimestampMixin, Base):
    __tablename__ = "records"
    __table_args__ = (Index("ix_records_kind_status_time", "kind", "status", "record_time"),)

    kind: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    stage: Mapped[str | None] = mapped_column(String(100))
    record_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
