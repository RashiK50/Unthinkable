import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, SmallInteger, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    topics: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    decisions: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    risks: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    open_questions: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    deadlines: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    next_meeting_agenda: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    health_score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    health_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    agent_warnings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
