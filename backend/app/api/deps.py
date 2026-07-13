"""Dependency-injection wiring. Routers depend on services; services get their
repositories here — nothing below the API layer imports FastAPI."""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import AuthUser, get_current_user
from app.db.session import get_session
from app.repositories.action_items import ActionItemRepository
from app.repositories.chat import ChatRepository
from app.repositories.chunks import ChunkRepository
from app.repositories.events import EventRepository
from app.repositories.meetings import MeetingRepository
from app.repositories.reports import ReportRepository
from app.repositories.transcripts import TranscriptRepository
from app.services.analytics import AnalyticsService
from app.services.chat import ChatService
from app.services.dashboard import DashboardService
from app.services.email import EmailService
from app.services.exports import ExportService
from app.services.meetings import MeetingService
from app.services.storage import StorageClient

SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
UserDep = Annotated[AuthUser, Depends(get_current_user)]


def _meeting_service(session: SessionDep, settings: SettingsDep) -> MeetingService:
    return MeetingService(
        meetings=MeetingRepository(session),
        reports=ReportRepository(session),
        transcripts=TranscriptRepository(session),
        events=EventRepository(session),
        storage=StorageClient(settings),
        settings=settings,
    )


def _chat_service(session: SessionDep, settings: SettingsDep) -> ChatService:
    return ChatService(
        meetings=MeetingRepository(session),
        chunks=ChunkRepository(session),
        chat=ChatRepository(session),
        settings=settings,
    )


def _analytics_service(session: SessionDep) -> AnalyticsService:
    return AnalyticsService(
        meetings=MeetingRepository(session),
        transcripts=TranscriptRepository(session),
        reports=ReportRepository(session),
    )


def _export_service(session: SessionDep) -> ExportService:
    return ExportService(
        meetings=MeetingRepository(session),
        reports=ReportRepository(session),
        action_items=ActionItemRepository(session),
    )


def _email_service(session: SessionDep) -> EmailService:
    return EmailService(
        meetings=MeetingRepository(session),
        reports=ReportRepository(session),
        action_items=ActionItemRepository(session),
    )


def _dashboard_service(session: SessionDep) -> DashboardService:
    return DashboardService(
        meetings=MeetingRepository(session),
        reports=ReportRepository(session),
        action_items=ActionItemRepository(session),
    )


MeetingServiceDep = Annotated[MeetingService, Depends(_meeting_service)]
ChatServiceDep = Annotated[ChatService, Depends(_chat_service)]
AnalyticsServiceDep = Annotated[AnalyticsService, Depends(_analytics_service)]
ExportServiceDep = Annotated[ExportService, Depends(_export_service)]
EmailServiceDep = Annotated[EmailService, Depends(_email_service)]
DashboardServiceDep = Annotated[DashboardService, Depends(_dashboard_service)]
