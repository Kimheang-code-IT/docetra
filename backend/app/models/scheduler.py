import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDPrimaryKeyMixin


class MeetingSchedule(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "meeting_schedules"

    meeting_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    job_key: Mapped[str] = mapped_column(String(160), unique=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), default="scheduled")
