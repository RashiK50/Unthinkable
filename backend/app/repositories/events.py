from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import ProcessingEvent


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    def add(
        self, meeting_id: UUID, stage: str, status: str, detail: str | None = None
    ) -> ProcessingEvent:
        event = ProcessingEvent(meeting_id=meeting_id, stage=stage, status=status, detail=detail)
        self._s.add(event)
        return event

    async def list_for_meeting(self, meeting_id: UUID) -> list[ProcessingEvent]:
        stmt = (
            select(ProcessingEvent)
            .where(ProcessingEvent.meeting_id == meeting_id)
            .order_by(ProcessingEvent.created_at)
        )
        return list((await self._s.execute(stmt)).scalars().all())
