from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript import TranscriptChunk


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    def add_all(self, chunks: list[TranscriptChunk]) -> None:
        self._s.add_all(chunks)

    async def delete_for_meeting(self, meeting_id: UUID) -> None:
        await self._s.execute(
            delete(TranscriptChunk).where(TranscriptChunk.meeting_id == meeting_id)
        )

    async def search(
        self, meeting_id: UUID, embedding: list[float], k: int
    ) -> list[TranscriptChunk]:
        """Top-k cosine similarity within one meeting (pgvector HNSW index)."""
        stmt = (
            select(TranscriptChunk)
            .where(
                TranscriptChunk.meeting_id == meeting_id,
                TranscriptChunk.embedding.is_not(None),
            )
            .order_by(TranscriptChunk.embedding.cosine_distance(embedding))
            .limit(k)
        )
        return list((await self._s.execute(stmt)).scalars().all())
