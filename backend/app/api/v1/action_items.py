from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import MeetingServiceDep, SessionDep, UserDep
from app.core.exceptions import BadRequestError, NotFoundError
from app.models.action_item import ActionItem
from app.repositories.action_items import ActionItemRepository
from app.schemas.action_item import (
    PRIORITIES,
    STATUSES,
    ActionItemCreate,
    ActionItemOut,
    ActionItemUpdate,
)

router = APIRouter(tags=["action-items"])


@router.get("/meetings/{meeting_id}/action-items", response_model=list[ActionItemOut])
async def list_items(
    meeting_id: UUID, user: UserDep, service: MeetingServiceDep, session: SessionDep
) -> list[ActionItemOut]:
    await service.get_owned(user, meeting_id)
    items = await ActionItemRepository(session).list_for_meeting(meeting_id)
    return [ActionItemOut.model_validate(i) for i in items]


@router.post(
    "/meetings/{meeting_id}/action-items",
    response_model=ActionItemOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_item(
    meeting_id: UUID,
    payload: ActionItemCreate,
    user: UserDep,
    service: MeetingServiceDep,
    session: SessionDep,
) -> ActionItemOut:
    await service.get_owned(user, meeting_id)
    if payload.priority not in PRIORITIES:
        raise BadRequestError(f"priority must be one of {sorted(PRIORITIES)}")
    repo = ActionItemRepository(session)
    existing = await repo.list_for_meeting(meeting_id)
    item = repo.add(
        ActionItem(
            meeting_id=meeting_id,
            task=payload.task.strip(),
            owner=payload.owner,
            due_date=payload.due_date,
            priority=payload.priority,
            sort_order=len(existing),
        )
    )
    await session.flush()
    return ActionItemOut.model_validate(item)


@router.patch("/action-items/{item_id}", response_model=ActionItemOut)
async def update_item(
    item_id: UUID, payload: ActionItemUpdate, user: UserDep, session: SessionDep
) -> ActionItemOut:
    item = await ActionItemRepository(session).get_owned(item_id, user.id)
    if item is None:
        raise NotFoundError("Action item not found")
    data = payload.model_dump(exclude_unset=True)
    if "priority" in data and data["priority"] not in PRIORITIES:
        raise BadRequestError(f"priority must be one of {sorted(PRIORITIES)}")
    if "status" in data and data["status"] not in STATUSES:
        raise BadRequestError(f"status must be one of {sorted(STATUSES)}")
    for field, value in data.items():
        setattr(item, field, value)
    return ActionItemOut.model_validate(item)


@router.delete("/action-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: UUID, user: UserDep, session: SessionDep) -> None:
    repo = ActionItemRepository(session)
    item = await repo.get_owned(item_id, user.id)
    if item is None:
        raise NotFoundError("Action item not found")
    await repo.delete(item)
