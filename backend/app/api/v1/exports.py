from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.api.deps import EmailServiceDep, ExportServiceDep, UserDep
from app.schemas.report import EmailDraft, EmailRequest

router = APIRouter(prefix="/meetings", tags=["exports"])


@router.get("/{meeting_id}/export")
async def export_meeting(
    meeting_id: UUID,
    user: UserDep,
    service: ExportServiceDep,
    format: str = Query(pattern="^(pdf|md|txt)$"),
) -> Response:
    file = await service.export(user, meeting_id, format)
    return Response(
        content=file.content,
        media_type=file.media_type,
        headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
    )


@router.post("/{meeting_id}/follow-up-email", response_model=EmailDraft)
async def follow_up_email(
    meeting_id: UUID, payload: EmailRequest, user: UserDep, service: EmailServiceDep
) -> EmailDraft:
    return await service.draft(user, meeting_id, payload.tone)
