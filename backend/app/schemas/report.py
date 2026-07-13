from typing import Any

from pydantic import BaseModel, ConfigDict


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    executive_summary: str
    topics: list[Any]
    decisions: list[Any]
    risks: list[Any]
    open_questions: list[Any]
    deadlines: list[Any]
    next_meeting_agenda: list[Any]
    health_score: int
    health_breakdown: dict[str, Any]
    agent_warnings: dict[str, Any]
    model: str


class SpeakerStat(BaseModel):
    label: str
    display_name: str
    talk_time_ms: int
    contribution_count: int
    share: float


class TopicSpeakerRow(BaseModel):
    topic: str
    speakers: dict[str, int]  # display_name -> ms spoken inside topic window


class AnalyticsOut(BaseModel):
    speakers: list[SpeakerStat]
    topics_by_speaker: list[TopicSpeakerRow]


class EmailRequest(BaseModel):
    tone: str = "professional"  # professional | friendly | brief


class EmailDraft(BaseModel):
    subject: str
    body: str
