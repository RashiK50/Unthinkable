from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PRIORITIES = {"low", "medium", "high", "urgent"}
STATUSES = {"open", "in_progress", "done", "blocked"}


class ActionItemCreate(BaseModel):
    task: str = Field(min_length=1)
    owner: str | None = None
    due_date: date | None = None
    priority: str = "medium"


class ActionItemUpdate(BaseModel):
    task: str | None = None
    owner: str | None = None
    due_date: date | None = None
    priority: str | None = None
    status: str | None = None


class ActionItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    meeting_id: UUID
    task: str
    owner: str | None
    due_date: date | None
    priority: str
    status: str
    sort_order: int
    created_at: datetime
    updated_at: datetime
