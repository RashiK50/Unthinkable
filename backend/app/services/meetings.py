import re
import uuid
from datetime import UTC, datetime

from app.core.config import Settings
from app.core.exceptions import BadRequestError, NotFoundError, PayloadTooLargeError
from app.core.security import AuthUser
from app.models.meeting import Meeting
from app.repositories.events import EventRepository
from app.repositories.meetings import MeetingRepository
from app.repositories.reports import ReportRepository
from app.repositories.transcripts import TranscriptRepository
from app.schemas.meeting import (
    MeetingCreate,
    MeetingCreated,
    MeetingDetail,
    MeetingOut,
    MeetingStatus,
    MeetingUpdate,
    StageStatus,
    UploadTarget,
)
from app.schemas.report import ReportOut
from app.schemas.transcript import SpeakerOut
from app.services.storage import StorageClient

_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")


class MeetingService:
    def __init__(
        self,
        meetings: MeetingRepository,
        reports: ReportRepository,
        transcripts: TranscriptRepository,
        events: EventRepository,
        storage: StorageClient,
        settings: Settings,
    ) -> None:
        self._meetings = meetings
        self._reports = reports
        self._transcripts = transcripts
        self._events = events
        self._storage = storage
        self._settings = settings

    async def create(self, user: AuthUser, payload: MeetingCreate) -> MeetingCreated:
        # Reject early — before the user sits through a 20-minute upload.
        ext = payload.filename.rsplit(".", 1)[-1].lower() if "." in payload.filename else ""
        if ext not in self._settings.allowed_audio_extensions:
            raise BadRequestError(
                f"Unsupported file type '.{ext}'. "
                f"Allowed: {', '.join(sorted(self._settings.allowed_audio_extensions))}"
            )
        if payload.size_bytes > self._settings.max_upload_bytes:
            raise PayloadTooLargeError(
                f"File exceeds {self._settings.max_upload_bytes // (1024 * 1024)} MB limit"
            )

        meeting_id = uuid.uuid4()
        safe_name = _SAFE_FILENAME.sub("_", payload.filename)[-100:]
        path = f"{user.id}/{meeting_id}/{safe_name}"

        # Timestamps set explicitly: this object is serialized to MeetingOut
        # before the first flush, so column defaults haven't fired yet.
        now = datetime.now(UTC)
        meeting = Meeting(
            id=meeting_id,
            user_id=user.id,
            title=payload.title.strip(),
            status="uploading",
            audio_path=path,
            audio_mime=payload.content_type,
            audio_size_bytes=payload.size_bytes,
            created_at=now,
            updated_at=now,
        )
        self._meetings.add(meeting)
        signed_url = await self._storage.create_signed_upload_url(path)
        return MeetingCreated(
            meeting=MeetingOut.model_validate(meeting),
            upload=UploadTarget(
                signed_url=signed_url,
                path=path,
                expires_in=self._settings.signed_url_ttl_seconds,
            ),
        )

    async def list(
        self, user: AuthUser, q: str | None, status: str | None, page: int, page_size: int
    ) -> tuple[list[MeetingOut], int]:
        items, total = await self._meetings.list(user.id, q, status, page, page_size)
        return [MeetingOut.model_validate(m) for m in items], total

    async def get_owned(self, user: AuthUser, meeting_id: uuid.UUID) -> Meeting:
        meeting = await self._meetings.get_owned(meeting_id, user.id)
        if meeting is None:
            raise NotFoundError("Meeting not found")
        return meeting

    async def detail(self, user: AuthUser, meeting_id: uuid.UUID) -> MeetingDetail:
        meeting = await self.get_owned(user, meeting_id)
        report = await self._reports.get(meeting_id)
        speakers = await self._transcripts.get_speakers(meeting_id)
        return MeetingDetail(
            meeting=MeetingOut.model_validate(meeting),
            report=ReportOut.model_validate(report) if report else None,
            speakers=[SpeakerOut.model_validate(s) for s in speakers],
        )

    async def status(self, user: AuthUser, meeting_id: uuid.UUID) -> MeetingStatus:
        meeting = await self.get_owned(user, meeting_id)
        events = await self._events.list_for_meeting(meeting_id)
        # Latest event per stage, in order of first appearance.
        order: list[str] = []
        latest: dict[str, StageStatus] = {}
        for e in events:
            if e.stage not in latest:
                order.append(e.stage)
            latest[e.stage] = StageStatus(
                stage=e.stage, status=e.status, detail=e.detail, at=e.created_at
            )
        return MeetingStatus(
            status=meeting.status,
            error_message=meeting.error_message,
            stages=[latest[s] for s in order],
        )

    async def rename(
        self, user: AuthUser, meeting_id: uuid.UUID, payload: MeetingUpdate
    ) -> MeetingOut:
        meeting = await self.get_owned(user, meeting_id)
        meeting.title = payload.title.strip()
        return MeetingOut.model_validate(meeting)

    async def delete(self, user: AuthUser, meeting_id: uuid.UUID) -> None:
        meeting = await self.get_owned(user, meeting_id)
        if meeting.audio_path:
            await self._storage.delete_object(meeting.audio_path)
        await self._meetings.delete(meeting)
