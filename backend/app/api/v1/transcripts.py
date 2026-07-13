from uuid import UUID

from fastapi import APIRouter

from app.api.deps import MeetingServiceDep, SessionDep, UserDep
from app.core.exceptions import NotFoundError
from app.repositories.transcripts import TranscriptRepository
from app.schemas.transcript import SegmentOut, SpeakerOut, SpeakerUpdate, TranscriptOut

router = APIRouter(prefix="/meetings", tags=["transcripts"])


@router.get("/{meeting_id}/transcript", response_model=TranscriptOut)
async def get_transcript(
    meeting_id: UUID, user: UserDep, service: MeetingServiceDep, session: SessionDep
) -> TranscriptOut:
    await service.get_owned(user, meeting_id)
    repo = TranscriptRepository(session)
    segments = await repo.get_segments(meeting_id)
    speakers = await repo.get_speakers(meeting_id)
    return TranscriptOut(
        segments=[SegmentOut.model_validate(s) for s in segments],
        speakers=[SpeakerOut.model_validate(s) for s in speakers],
    )


@router.patch("/{meeting_id}/speakers/{speaker_id}", response_model=SpeakerOut)
async def rename_speaker(
    meeting_id: UUID,
    speaker_id: UUID,
    payload: SpeakerUpdate,
    user: UserDep,
    service: MeetingServiceDep,
    session: SessionDep,
) -> SpeakerOut:
    await service.get_owned(user, meeting_id)
    speaker = await TranscriptRepository(session).get_speaker(speaker_id, meeting_id)
    if speaker is None:
        raise NotFoundError("Speaker not found")
    speaker.display_name = payload.display_name.strip()
    return SpeakerOut.model_validate(speaker)
