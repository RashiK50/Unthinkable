"""Dashboard stats and cross-meeting insights.

Insights are deterministic aggregation over stored reports — cheap, explainable,
no extra LLM spend (architecture doc §5 upgrade table)."""
from datetime import UTC, datetime, timedelta

from app.core.security import AuthUser
from app.repositories.action_items import ActionItemRepository
from app.repositories.meetings import MeetingRepository
from app.repositories.reports import ReportRepository
from app.schemas.dashboard import DashboardInsights, DashboardStats, HealthPoint, Insight


class DashboardService:
    def __init__(
        self,
        meetings: MeetingRepository,
        reports: ReportRepository,
        action_items: ActionItemRepository,
    ) -> None:
        self._meetings = meetings
        self._reports = reports
        self._items = action_items

    async def stats(self, user: AuthUser) -> DashboardStats:
        now = datetime.now(UTC)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        today = now.date()

        total = await self._meetings.count_all(user.id)
        this_week = await self._meetings.count_since(user.id, week_ago)
        seconds = await self._meetings.total_duration_seconds(user.id)
        open_items = await self._items.count_open(user.id)
        overdue = await self._items.overdue(user.id, today)
        avg_health = await self._reports.avg_health(user.id)
        trend = await self._reports.health_trend(user.id, month_ago)

        return DashboardStats(
            total_meetings=total,
            meetings_this_week=this_week,
            hours_processed=round(seconds / 3600, 1),
            open_action_items=open_items,
            overdue_action_items=len(overdue),
            avg_health_score=round(avg_health, 1) if avg_health is not None else None,
            health_trend=[HealthPoint(date=d.date(), score=round(s, 1)) for d, s in trend],
        )

    async def insights(self, user: AuthUser) -> DashboardInsights:
        insights: list[Insight] = []
        today = datetime.now(UTC).date()

        overdue = await self._items.overdue(user.id, today)
        if overdue:
            by_owner: dict[str, int] = {}
            for item in overdue:
                owner = item.owner or "unassigned"
                by_owner[owner] = by_owner.get(owner, 0) + 1
            worst = max(by_owner, key=lambda k: by_owner[k])
            insights.append(
                Insight(
                    kind="overdue",
                    message=f"{len(overdue)} action item(s) are overdue - "
                    f"most ({by_owner[worst]}) owned by {worst}.",
                )
            )

        recent = await self._reports.recent_with_meetings(user.id, limit=10)
        unresolved = sum(len(r.open_questions) for r, _ in recent)
        if unresolved >= 3:
            insights.append(
                Insight(
                    kind="unresolved",
                    message=f"{unresolved} open questions across your last "
                    f"{len(recent)} meetings - consider a decision-focused session.",
                )
            )
        low = [(r, m) for r, m in recent if r.health_score < 55]
        if low:
            worst_report, worst_meeting = min(low, key=lambda pair: pair[0].health_score)
            insights.append(
                Insight(
                    kind="low_health",
                    message=f'"{worst_meeting.title}" scored {worst_report.health_score}/100 - '
                    "check its health breakdown for what went wrong.",
                )
            )
        if not insights and recent:
            insights.append(
                Insight(kind="ok", message="No red flags across your recent meetings. Keep it up.")
            )
        return DashboardInsights(insights=insights)
