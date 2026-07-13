from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting
from app.models.report import Report


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    def add(self, report: Report) -> Report:
        self._s.add(report)
        return report

    async def get(self, meeting_id: UUID) -> Report | None:
        stmt = select(Report).where(Report.meeting_id == meeting_id)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def delete_for_meeting(self, meeting_id: UUID) -> None:
        await self._s.execute(delete(Report).where(Report.meeting_id == meeting_id))

    async def avg_health(self, user_id: UUID) -> float | None:
        stmt = (
            select(func.avg(Report.health_score))
            .join(Meeting, Meeting.id == Report.meeting_id)
            .where(Meeting.user_id == user_id)
        )
        value = (await self._s.execute(stmt)).scalar_one_or_none()
        return float(value) if value is not None else None

    async def health_trend(self, user_id: UUID, since: datetime) -> list[tuple[datetime, float]]:
        day = func.date_trunc("day", Report.created_at)
        stmt = (
            select(day, func.avg(Report.health_score))
            .join(Meeting, Meeting.id == Report.meeting_id)
            .where(Meeting.user_id == user_id, Report.created_at >= since)
            .group_by(day)
            .order_by(day)
        )
        rows = (await self._s.execute(stmt)).all()
        return [(r[0], float(r[1])) for r in rows]

    async def recent_with_meetings(
        self, user_id: UUID, limit: int
    ) -> list[tuple[Report, Meeting]]:
        stmt = (
            select(Report, Meeting)
            .join(Meeting, Meeting.id == Report.meeting_id)
            .where(Meeting.user_id == user_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
        )
        return [(r, m) for r, m in (await self._s.execute(stmt)).all()]
