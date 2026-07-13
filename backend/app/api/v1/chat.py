from uuid import UUID

from fastapi import APIRouter

from app.api.deps import ChatServiceDep, UserDep
from app.schemas.chat import ChatAnswer, ChatMessageOut, ChatRequest

router = APIRouter(prefix="/meetings", tags=["chat"])


@router.get("/{meeting_id}/chat", response_model=list[ChatMessageOut])
async def chat_history(
    meeting_id: UUID, user: UserDep, service: ChatServiceDep
) -> list[ChatMessageOut]:
    return await service.history(user, meeting_id)


@router.post("/{meeting_id}/chat", response_model=ChatAnswer)
async def ask(
    meeting_id: UUID, payload: ChatRequest, user: UserDep, service: ChatServiceDep
) -> ChatAnswer:
    return await service.ask(user, meeting_id, payload.message)
