"""In-process pipeline dispatcher — the deliberately boring MVP job runner.

The seam a real queue would slot into (architecture doc §5): swap `start` to
enqueue into Celery/Arq and nothing upstream changes. Duplicate-start protection
lives here so the API can return 409 instead of double-processing.
"""
import asyncio
from uuid import UUID

import structlog

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.services.processing import ProcessingService

logger = structlog.get_logger()


class PipelineDispatcher:
    def __init__(self) -> None:
        self._tasks: dict[UUID, asyncio.Task[None]] = {}

    def is_running(self, meeting_id: UUID) -> bool:
        task = self._tasks.get(meeting_id)
        return task is not None and not task.done()

    def start(self, meeting_id: UUID) -> None:
        if self.is_running(meeting_id):
            return
        service = ProcessingService(get_session_factory(), get_settings())
        task = asyncio.create_task(service.run(meeting_id), name=f"pipeline-{meeting_id}")
        self._tasks[meeting_id] = task
        task.add_done_callback(lambda t: self._on_done(meeting_id, t))

    def _on_done(self, meeting_id: UUID, task: asyncio.Task[None]) -> None:
        self._tasks.pop(meeting_id, None)
        if not task.cancelled() and task.exception() is not None:
            # ProcessingService.run catches everything; this is belt-and-braces.
            logger.error("dispatcher_task_error", meeting_id=str(meeting_id))


dispatcher = PipelineDispatcher()
