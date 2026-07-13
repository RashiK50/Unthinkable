from uuid import UUID

from fastapi import APIRouter

from app.api.deps import AnalyticsServiceDep, MeetingServiceDep, SessionDep, UserDep
from app.core.exceptions import NotFoundError
from app.repositories.reports import ReportRepository
from app.schemas.report import AnalyticsOut, ReportOut

router = APIRouter(prefix="/meetings", tags=["reports"])


@router.get("/{meeting_id}/report", response_model=ReportOut)
async def get_report(
    meeting_id: UUID, user: UserDep, service: MeetingServiceDep, session: SessionDep
) -> ReportOut:
    await service.get_owned(user, meeting_id)
    report = await ReportRepository(session).get(meeting_id)
    if report is None:
        raise NotFoundError("No report for this meeting yet")
    return ReportOut.model_validate(report)


@router.get("/{meeting_id}/analytics", response_model=AnalyticsOut)
async def get_analytics(
    meeting_id: UUID, user: UserDep, service: AnalyticsServiceDep
) -> AnalyticsOut:
    return await service.compute(user, meeting_id)
