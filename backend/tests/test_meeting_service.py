"""Service-level tests with fakes — no database, no network.
This is the payoff of the repository seam (architecture doc §2.4)."""
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.exceptions import BadRequestError, PayloadTooLargeError
from app.core.security import AuthUser
from app.schemas.meeting import MeetingCreate
from app.services.meetings import MeetingService


def make_settings() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://x/x",
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="k",
        supabase_jwt_secret="s",
        gemini_api_key="g",
    )


class FakeMeetingRepo:
    def __init__(self) -> None:
        self.added = []

    def add(self, meeting):
        self.added.append(meeting)
        return meeting


class FakeStorage:
    async def create_signed_upload_url(self, path: str) -> str:
        return f"https://signed.example/{path}"


def make_service() -> tuple[MeetingService, FakeMeetingRepo]:
    repo = FakeMeetingRepo()
    service = MeetingService(
        meetings=repo,  # type: ignore[arg-type]
        reports=None,  # type: ignore[arg-type]
        transcripts=None,  # type: ignore[arg-type]
        events=None,  # type: ignore[arg-type]
        storage=FakeStorage(),  # type: ignore[arg-type]
        settings=make_settings(),
    )
    return service, repo


USER = AuthUser(id=uuid4(), email="test@example.com")


async def test_create_rejects_unsupported_extension() -> None:
    service, _ = make_service()
    with pytest.raises(BadRequestError):
        await service.create(
            USER,
            MeetingCreate(title="X", filename="notes.docx", content_type="x", size_bytes=100),
        )


async def test_create_rejects_oversized_file() -> None:
    service, _ = make_service()
    with pytest.raises(PayloadTooLargeError):
        await service.create(
            USER,
            MeetingCreate(
                title="X",
                filename="a.mp3",
                content_type="audio/mpeg",
                size_bytes=501 * 1024 * 1024,
            ),
        )


async def test_create_returns_user_scoped_path_and_signed_url() -> None:
    service, repo = make_service()
    result = await service.create(
        USER,
        MeetingCreate(
            title="  Q3 Sync  ", filename="q3 sync!.mp3", content_type="audio/mpeg", size_bytes=100
        ),
    )
    assert len(repo.added) == 1
    meeting = repo.added[0]
    assert meeting.title == "Q3 Sync"
    assert meeting.status == "uploading"
    # Path is {user_id}/{meeting_id}/{sanitized}: storage RLS depends on this shape.
    assert result.upload.path.startswith(f"{USER.id}/")
    assert result.upload.path.endswith("q3_sync_.mp3")
    assert result.upload.signed_url.startswith("https://signed.example/")
