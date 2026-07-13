from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import MeetingServiceDep, UserDep
from app.core.exceptions import ConflictError
from app.schemas.common import Page
from app.schemas.meeting import (
    MeetingCreate,
    MeetingCreated,
    MeetingDetail,
    MeetingOut,
    MeetingStatus,
    MeetingUpdate,
    ProcessAccepted,
)
from app.workers.dispatcher import dispatcher

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.post("", response_model=MeetingCreated, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    payload: MeetingCreate, user: UserDep, service: MeetingServiceDep
) -> MeetingCreated:
    return await service.create(user, payload)


@router.get("", response_model=Page[MeetingOut])
async def list_meetings(
    user: UserDep,
    service: MeetingServiceDep,
    q: str | None = Query(default=None, max_length=200),
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Page[MeetingOut]:
    items, total = await service.list(user, q, status_filter, page, page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{meeting_id}", response_model=MeetingDetail)
async def get_meeting(
    meeting_id: UUID, user: UserDep, service: MeetingServiceDep
) -> MeetingDetail:
    return await service.detail(user, meeting_id)


@router.get("/{meeting_id}/status", response_model=MeetingStatus)
async def get_status(
    meeting_id: UUID, user: UserDep, service: MeetingServiceDep
) -> MeetingStatus:
    return await service.status(user, meeting_id)


@router.patch("/{meeting_id}", response_model=MeetingOut)
async def rename_meeting(
    meeting_id: UUID, payload: MeetingUpdate, user: UserDep, service: MeetingServiceDep
) -> MeetingOut:
    return await service.rename(user, meeting_id, payload)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(meeting_id: UUID, user: UserDep, service: MeetingServiceDep) -> None:
    await service.delete(user, meeting_id)


@router.post(
    "/{meeting_id}/process",
    response_model=ProcessAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def process_meeting(
    meeting_id: UUID, user: UserDep, service: MeetingServiceDep
) -> ProcessAccepted:
    meeting = await service.get_owned(user, meeting_id)
    if dispatcher.is_running(meeting_id) or meeting.status in ("transcribing", "analyzing"):
        raise ConflictError("This meeting is already being processed")
    if meeting.status == "completed":
        raise ConflictError("This meeting is already processed")
    dispatcher.start(meeting_id)
    return ProcessAccepted(status="queued")
