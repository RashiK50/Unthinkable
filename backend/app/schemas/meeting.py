from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.report import ReportOut
from app.schemas.transcript import SpeakerOut


class MeetingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    filename: str = Field(min_length=1)
    content_type: str
    size_bytes: int = Field(gt=0)


class MeetingUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=300)


class MeetingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    status: str
    audio_size_bytes: int | None = None
    duration_seconds: int | None = None
    language: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class UploadTarget(BaseModel):
    signed_url: str
    path: str
    expires_in: int


class MeetingCreated(BaseModel):
    meeting: MeetingOut
    upload: UploadTarget


class MeetingDetail(BaseModel):
    meeting: MeetingOut
    report: ReportOut | None
    speakers: list[SpeakerOut]


class StageStatus(BaseModel):
    stage: str
    status: str
    detail: str | None = None
    at: datetime


class MeetingStatus(BaseModel):
    status: str
    error_message: str | None = None
    stages: list[StageStatus]


class ProcessAccepted(BaseModel):
    status: str
