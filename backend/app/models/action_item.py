import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

ACTION_PRIORITIES = ("low", "medium", "high", "urgent")
ACTION_STATUSES = ("open", "in_progress", "done", "blocked")

priority_enum = ENUM(*ACTION_PRIORITIES, name="action_item_priority", create_type=False)
status_enum = ENUM(*ACTION_STATUSES, name="action_item_status", create_type=False)


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date)
    priority: Mapped[str] = mapped_column(priority_enum, nullable=False, default="medium")
    status: Mapped[str] = mapped_column(status_enum, nullable=False, default="open")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Client-side default too: ActionItemOut is serialized before commit.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
