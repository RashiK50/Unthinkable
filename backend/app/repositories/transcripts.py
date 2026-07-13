from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcript import Speaker, Transcript, TranscriptSegment


class TranscriptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    def add_transcript(self, transcript: Transcript) -> Transcript:
        self._s.add(transcript)
        return transcript

    def add_segments(self, segments: list[TranscriptSegment]) -> None:
        self._s.add_all(segments)

    def add_speakers(self, speakers: list[Speaker]) -> None:
        self._s.add_all(speakers)

    async def get_transcript(self, meeting_id: UUID) -> Transcript | None:
        stmt = select(Transcript).where(Transcript.meeting_id == meeting_id)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def get_segments(self, meeting_id: UUID) -> list[TranscriptSegment]:
        stmt = (
            select(TranscriptSegment)
            .where(TranscriptSegment.meeting_id == meeting_id)
            .order_by(TranscriptSegment.start_ms)
        )
        return list((await self._s.execute(stmt)).scalars().all())

    async def get_speakers(self, meeting_id: UUID) -> list[Speaker]:
        stmt = select(Speaker).where(Speaker.meeting_id == meeting_id).order_by(Speaker.label)
        return list((await self._s.execute(stmt)).scalars().all())

    async def get_speaker(self, speaker_id: UUID, meeting_id: UUID) -> Speaker | None:
        stmt = select(Speaker).where(Speaker.id == speaker_id, Speaker.meeting_id == meeting_id)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def delete_for_meeting(self, meeting_id: UUID) -> None:
        await self._s.execute(
            delete(TranscriptSegment).where(TranscriptSegment.meeting_id == meeting_id)
        )
        await self._s.execute(delete(Speaker).where(Speaker.meeting_id == meeting_id))
        await self._s.execute(delete(Transcript).where(Transcript.meeting_id == meeting_id))
