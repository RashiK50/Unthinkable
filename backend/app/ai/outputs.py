"""Pydantic contracts for every agent's structured output.
These double as the Gemini response_schema — one source of truth."""
from pydantic import BaseModel, Field


class CleanedTranscript(BaseModel):
    cleaned_text: str


class Topic(BaseModel):
    title: str
    summary: str
    start_ms: int | None = None
    end_ms: int | None = None


class TopicList(BaseModel):
    topics: list[Topic]


class Decision(BaseModel):
    decision: str
    context: str
    made_by: str | None = None


class OpenQuestion(BaseModel):
    question: str
    raised_by: str | None = None


class DecisionResult(BaseModel):
    decisions: list[Decision]
    open_questions: list[OpenQuestion]


class ExtractedActionItem(BaseModel):
    task: str
    owner: str | None = None
    due_date: str | None = Field(default=None, description="ISO date YYYY-MM-DD if inferable")
    priority: str = Field(default="medium", description="low|medium|high|urgent")


class ActionItemList(BaseModel):
    action_items: list[ExtractedActionItem]


class Risk(BaseModel):
    description: str
    kind: str = Field(description="risk|blocker")
    severity: str = Field(description="low|medium|high")


class RiskList(BaseModel):
    risks: list[Risk]


class Deadline(BaseModel):
    item: str
    date_text: str
    date_normalized: str | None = Field(default=None, description="ISO date if resolvable")


class DeadlineList(BaseModel):
    deadlines: list[Deadline]


class SummaryResult(BaseModel):
    executive_summary: str
    next_meeting_agenda: list[str]
