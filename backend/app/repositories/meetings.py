from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting


class MeetingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    def add(self, meeting: Meeting) -> Meeting:
        self._s.add(meeting)
        return meeting

    async def get_owned(self, meeting_id: UUID, user_id: UUID) -> Meeting | None:
        stmt = select(Meeting).where(Meeting.id == meeting_id, Meeting.user_id == user_id)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def get(self, meeting_id: UUID) -> Meeting | None:
        return await self._s.get(Meeting, meeting_id)

    async def list(
        self,
        user_id: UUID,
        q: str | None,
        status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Meeting], int]:
        base = select(Meeting).where(Meeting.user_id == user_id)
        if q:
            base = base.where(or_(Meeting.title.ilike(f"%{q}%")))
        if status:
            base = base.where(Meeting.status == status)
        total = (
            await self._s.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        stmt = (
            base.order_by(Meeting.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list((await self._s.execute(stmt)).scalars().all())
        return items, total

    async def delete(self, meeting: Meeting) -> None:
        await self._s.delete(meeting)

    async def count_all(self, user_id: UUID) -> int:
        stmt = select(func.count()).select_from(Meeting).where(Meeting.user_id == user_id)
        return (await self._s.execute(stmt)).scalar_one()

    async def count_since(self, user_id: UUID, since: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(Meeting)
            .where(Meeting.user_id == user_id, Meeting.created_at >= since)
        )
        return (await self._s.execute(stmt)).scalar_one()

    async def total_duration_seconds(self, user_id: UUID) -> int:
        stmt = select(func.coalesce(func.sum(Meeting.duration_seconds), 0)).where(
            Meeting.user_id == user_id
        )
        return (await self._s.execute(stmt)).scalar_one()
