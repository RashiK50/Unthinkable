from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SpeakerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    label: str
    display_name: str


class SpeakerUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)


class SegmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    speaker_label: str
    start_ms: int
    end_ms: int
    text: str


class TranscriptOut(BaseModel):
    segments: list[SegmentOut]
    speakers: list[SpeakerOut]
