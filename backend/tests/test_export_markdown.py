from datetime import UTC, datetime
from uuid import uuid4

from app.models.action_item import ActionItem
from app.models.meeting import Meeting
from app.models.report import Report
from app.services.exports import _markdown_to_text, render_markdown


def build_fixtures() -> tuple[Meeting, Report, list[ActionItem]]:
    mid = uuid4()
    meeting = Meeting(
        id=mid,
        user_id=uuid4(),
        title="Q3 Planning Sync",
        status="completed",
        created_at=datetime(2026, 7, 12, tzinfo=UTC),
    )
    report = Report(
        meeting_id=mid,
        executive_summary="We aligned on Q3 priorities.",
        topics=[{"title": "Budget", "summary": "Re-forecast agreed."}],
        decisions=[{"decision": "Adopt Supabase", "context": "", "made_by": "Priya"}],
        risks=[{"description": "Owner unclear", "kind": "blocker", "severity": "high"}],
        open_questions=[{"question": "SOC2 before launch?"}],
        deadlines=[{"item": "Contract", "date_text": "next week", "date_normalized": "2026-07-19"}],
        next_meeting_agenda=["Review shortlist"],
        health_score=74,
        health_breakdown={},
        agent_warnings={},
        model="gemini-2.5-flash",
    )
    items = [
        ActionItem(
            meeting_id=mid, task="Send vendor quote", owner="Rahul", priority="high", status="open"
        )
    ]
    return meeting, report, items


def test_markdown_contains_every_report_section() -> None:
    md = render_markdown(*build_fixtures())
    for expected in [
        "# Q3 Planning Sync",
        "Health score: 74/100",
        "## Executive summary",
        "## Key topics",
        "## Decisions",
        "## Action items",
        "| Send vendor quote | Rahul |",
        "## Risks & blockers",
        "## Open questions",
        "## Deadlines",
        "2026-07-19",
        "## Suggested agenda for next meeting",
    ]:
        assert expected in md, f"missing: {expected}"


def test_txt_export_strips_markdown_tokens() -> None:
    md = render_markdown(*build_fixtures())
    text = _markdown_to_text(md)
    assert "##" not in text
    assert "**" not in text
    assert "Q3 Planning Sync" in text
