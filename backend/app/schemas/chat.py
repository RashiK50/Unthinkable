from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ChatSource(BaseModel):
    chunk_id: int
    start_ms: int | None = None
    end_ms: int | None = None


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    sources: list[Any]
    created_at: datetime


class ChatAnswer(BaseModel):
    answer: str
    sources: list[ChatSource]
