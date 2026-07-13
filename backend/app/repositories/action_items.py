from datetime import date
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_item import ActionItem
from app.models.meeting import Meeting


class ActionItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    def add(self, item: ActionItem) -> ActionItem:
        self._s.add(item)
        return item

    def add_all(self, items: list[ActionItem]) -> None:
        self._s.add_all(items)

    async def list_for_meeting(self, meeting_id: UUID) -> list[ActionItem]:
        stmt = (
            select(ActionItem)
            .where(ActionItem.meeting_id == meeting_id)
            .order_by(ActionItem.sort_order, ActionItem.created_at)
        )
        return list((await self._s.execute(stmt)).scalars().all())

    async def get_owned(self, item_id: UUID, user_id: UUID) -> ActionItem | None:
        stmt = (
            select(ActionItem)
            .join(Meeting, Meeting.id == ActionItem.meeting_id)
            .where(ActionItem.id == item_id, Meeting.user_id == user_id)
        )
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def delete(self, item: ActionItem) -> None:
        await self._s.delete(item)

    async def delete_for_meeting(self, meeting_id: UUID) -> None:
        await self._s.execute(delete(ActionItem).where(ActionItem.meeting_id == meeting_id))

    async def count_open(self, user_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(ActionItem)
            .join(Meeting, Meeting.id == ActionItem.meeting_id)
            .where(Meeting.user_id == user_id, ActionItem.status.in_(["open", "in_progress"]))
        )
        return (await self._s.execute(stmt)).scalar_one()

    async def overdue(self, user_id: UUID, today: date) -> list[ActionItem]:
        stmt = (
            select(ActionItem)
            .join(Meeting, Meeting.id == ActionItem.meeting_id)
            .where(
                Meeting.user_id == user_id,
                ActionItem.status.in_(["open", "in_progress"]),
                ActionItem.due_date.is_not(None),
                ActionItem.due_date < today,
            )
        )
        return list((await self._s.execute(stmt)).scalars().all())
