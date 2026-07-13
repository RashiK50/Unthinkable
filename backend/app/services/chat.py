"""RAG chat over one meeting's transcript (architecture doc §2.7).
Answers cite chunk timestamps so the UI can deep-link into the transcript."""
from uuid import UUID

from app.ai import llm, prompts
from app.core.config import Settings
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import AuthUser
from app.models.chat import ChatMessage
from app.repositories.chat import ChatRepository
from app.repositories.chunks import ChunkRepository
from app.repositories.meetings import MeetingRepository
from app.schemas.chat import ChatAnswer, ChatMessageOut, ChatSource
from app.services.processing import format_ms


class ChatService:
    def __init__(
        self,
        meetings: MeetingRepository,
        chunks: ChunkRepository,
        chat: ChatRepository,
        settings: Settings,
    ) -> None:
        self._meetings = meetings
        self._chunks = chunks
        self._chat = chat
        self._settings = settings

    async def history(self, user: AuthUser, meeting_id: UUID) -> list[ChatMessageOut]:
        if await self._meetings.get_owned(meeting_id, user.id) is None:
            raise NotFoundError("Meeting not found")
        messages = await self._chat.list_for_meeting(meeting_id, user.id)
        return [ChatMessageOut.model_validate(m) for m in messages]

    async def ask(self, user: AuthUser, meeting_id: UUID, message: str) -> ChatAnswer:
        meeting = await self._meetings.get_owned(meeting_id, user.id)
        if meeting is None:
            raise NotFoundError("Meeting not found")
        if meeting.status != "completed":
            raise ConflictError("Chat is available once the meeting has finished processing")

        self._chat.add(
            ChatMessage(meeting_id=meeting_id, user_id=user.id, role="user", content=message)
        )

        query_vec = (await llm.embed_texts([message]))[0]
        hits = await self._chunks.search(meeting_id, query_vec, self._settings.rag_top_k)

        if not hits:
            answer = (
                "I don't have a searchable transcript for this meeting "
                "(embeddings are unavailable), so I can't answer that."
            )
            sources: list[ChatSource] = []
        else:
            excerpts = "\n\n".join(
                f"[chunk {c.id} | {format_ms(c.start_ms or 0)}-{format_ms(c.end_ms or 0)}]\n"
                f"{c.content}"
                for c in hits
            )
            answer = await llm.generate_text(prompts.chat_prompt(message, excerpts))
            sources = [
                ChatSource(chunk_id=c.id, start_ms=c.start_ms, end_ms=c.end_ms) for c in hits[:3]
            ]

        self._chat.add(
            ChatMessage(
                meeting_id=meeting_id,
                user_id=user.id,
                role="assistant",
                content=answer,
                sources=[s.model_dump() for s in sources],
            )
        )
        return ChatAnswer(answer=answer, sources=sources)
