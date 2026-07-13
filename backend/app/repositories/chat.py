from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatMessage


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    def add(self, message: ChatMessage) -> ChatMessage:
        self._s.add(message)
        return message

    async def list_for_meeting(self, meeting_id: UUID, user_id: UUID) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.meeting_id == meeting_id, ChatMessage.user_id == user_id)
            .order_by(ChatMessage.created_at)
        )
        return list((await self._s.execute(stmt)).scalars().all())
