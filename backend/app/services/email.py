"""Follow-up email generation. We draft; the user sends from their own client —
no SMTP scope creep in v1 (wireframes doc §5)."""
import json
from uuid import UUID

from app.ai import llm, prompts
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import AuthUser
from app.repositories.action_items import ActionItemRepository
from app.repositories.meetings import MeetingRepository
from app.repositories.reports import ReportRepository
from app.schemas.report import EmailDraft

_ALLOWED_TONES = {"professional", "friendly", "brief"}


class EmailService:
    def __init__(
        self,
        meetings: MeetingRepository,
        reports: ReportRepository,
        action_items: ActionItemRepository,
    ) -> None:
        self._meetings = meetings
        self._reports = reports
        self._items = action_items

    async def draft(self, user: AuthUser, meeting_id: UUID, tone: str) -> EmailDraft:
        if tone not in _ALLOWED_TONES:
            tone = "professional"
        meeting = await self._meetings.get_owned(meeting_id, user.id)
        if meeting is None:
            raise NotFoundError("Meeting not found")
        report = await self._reports.get(meeting_id)
        if report is None:
            raise ConflictError("This meeting has no report yet")
        items = await self._items.list_for_meeting(meeting_id)

        report_block = json.dumps(
            {
                "date": meeting.created_at.date().isoformat(),
                "summary": report.executive_summary,
                "decisions": report.decisions,
                "action_items": [
                    {
                        "task": a.task,
                        "owner": a.owner,
                        "due_date": a.due_date.isoformat() if a.due_date else None,
                        "priority": a.priority,
                    }
                    for a in items
                ],
                "open_questions": report.open_questions,
                "deadlines": report.deadlines,
            },
            indent=1,
        )
        return await llm.generate_structured(
            prompts.email_prompt(tone, meeting.title, report_block), EmailDraft, temperature=0.5
        )
