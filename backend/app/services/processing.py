"""The pipeline runner: transcribe -> LangGraph agents -> persist -> embed.

Each phase commits in its own session so progress survives restarts and the
status endpoint always reflects reality. This service is invoked by the
PipelineDispatcher, never by an HTTP request directly.
"""
from datetime import date
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from structlog.typing import FilteringBoundLogger

from app.ai.graph import build_pipeline
from app.ai.llm import embed_texts
from app.core.config import Settings
from app.models.action_item import ACTION_PRIORITIES, ActionItem
from app.models.report import Report
from app.models.transcript import Speaker, Transcript, TranscriptChunk, TranscriptSegment
from app.repositories.action_items import ActionItemRepository
from app.repositories.chunks import ChunkRepository
from app.repositories.events import EventRepository
from app.repositories.meetings import MeetingRepository
from app.repositories.reports import ReportRepository
from app.repositories.transcripts import TranscriptRepository
from app.services.storage import StorageClient
from app.transcription.base import SegmentIn, get_provider

logger = structlog.get_logger()

CHUNK_MAX_CHARS = 1200


def format_ms(ms: int) -> str:
    total_s = ms // 1000
    return f"{total_s // 60:02d}:{total_s % 60:02d}"


def build_transcript_text(
    segments: list[SegmentIn], display: dict[str, str], max_chars: int
) -> str:
    lines = [
        f"[{format_ms(seg.start_ms)}] "
        f"{display.get(seg.speaker_label, seg.speaker_label)}: {seg.text}"
        for seg in segments
    ]
    text = "\n".join(lines)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[... transcript truncated for analysis ...]"
    return text


def compute_talk_shares(segments: list[SegmentIn], display: dict[str, str]) -> dict[str, float]:
    totals: dict[str, int] = {}
    for seg in segments:
        name = display.get(seg.speaker_label, seg.speaker_label)
        totals[name] = totals.get(name, 0) + max(0, seg.end_ms - seg.start_ms)
    grand = sum(totals.values())
    if grand == 0:
        return {}
    return {name: ms / grand for name, ms in totals.items()}


def build_chunks(
    segments: list[SegmentIn], display: dict[str, str], max_chars: int = CHUNK_MAX_CHARS
) -> list[tuple[str, int | None, int | None]]:
    """Group consecutive segments into ~max_chars chunks, keeping speaker + time context."""
    chunks: list[tuple[str, int | None, int | None]] = []
    buf: list[str] = []
    size = 0
    start: int | None = None
    end: int | None = None
    for seg in segments:
        speaker = display.get(seg.speaker_label, seg.speaker_label)
        line = f"{speaker} ({format_ms(seg.start_ms)}): {seg.text}"
        if buf and size + len(line) > max_chars:
            chunks.append(("\n".join(buf), start, end))
            buf, size, start = [], 0, None
        if start is None:
            start = seg.start_ms
        end = seg.end_ms
        buf.append(line)
        size += len(line)
    if buf:
        chunks.append(("\n".join(buf), start, end))
    return chunks


class ProcessingService:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], settings: Settings
    ) -> None:
        self._factory = session_factory
        self._settings = settings

    async def run(self, meeting_id: UUID) -> None:
        log = logger.bind(meeting_id=str(meeting_id))
        try:
            await self._run(meeting_id, log)
            log.info("pipeline_completed")
        except Exception as exc:
            log.exception("pipeline_failed")
            await self._record(meeting_id, "pipeline", "failed", str(exc)[:500])
            await self._set_status(meeting_id, "failed", error=str(exc)[:1000])

    # -- internals ---------------------------------------------------------

    async def _record(
        self, meeting_id: UUID, stage: str, status: str, detail: str | None = None
    ) -> None:
        async with self._factory() as session:
            EventRepository(session).add(meeting_id, stage, status, detail)
            await session.commit()

    async def _set_status(self, meeting_id: UUID, status: str, error: str | None = None) -> None:
        async with self._factory() as session:
            meeting = await MeetingRepository(session).get(meeting_id)
            if meeting is not None:
                meeting.status = status
                meeting.error_message = error
                await session.commit()

    async def _run(self, meeting_id: UUID, log: FilteringBoundLogger) -> None:
        # Phase 1 — load and mark transcribing.
        async with self._factory() as session:
            meeting = await MeetingRepository(session).get(meeting_id)
            if meeting is None or not meeting.audio_path:
                raise RuntimeError("Meeting missing or has no uploaded audio")
            title = meeting.title
            meeting_date: date = meeting.created_at.date()
            audio_path = meeting.audio_path
            meeting.status = "transcribing"
            meeting.error_message = None
            await session.commit()

        # Phase 2 — transcribe from a signed URL (bytes never touch this process for Deepgram).
        await self._record(meeting_id, "transcription", "started")
        storage = StorageClient(self._settings)
        audio_url = await storage.create_signed_download_url(audio_path)
        result = await get_provider(self._settings).transcribe(audio_url)

        # Phase 3 — wipe derived data (idempotent reprocessing) and persist the transcript.
        labels = sorted({s.speaker_label for s in result.segments}) or ["S1"]
        display = {label: f"Speaker {i + 1}" for i, label in enumerate(labels)}
        async with self._factory() as session:
            transcripts = TranscriptRepository(session)
            await ReportRepository(session).delete_for_meeting(meeting_id)
            await ActionItemRepository(session).delete_for_meeting(meeting_id)
            await ChunkRepository(session).delete_for_meeting(meeting_id)
            await transcripts.delete_for_meeting(meeting_id)

            transcripts.add_transcript(
                Transcript(
                    meeting_id=meeting_id,
                    raw_text=result.raw_text,
                    provider=result.provider,
                    word_count=len(result.raw_text.split()),
                )
            )
            transcripts.add_segments(
                [
                    TranscriptSegment(
                        meeting_id=meeting_id,
                        speaker_label=s.speaker_label,
                        start_ms=s.start_ms,
                        end_ms=s.end_ms,
                        text=s.text,
                    )
                    for s in result.segments
                ]
            )
            transcripts.add_speakers(
                [
                    Speaker(meeting_id=meeting_id, label=label, display_name=display[label])
                    for label in labels
                ]
            )
            meeting = await MeetingRepository(session).get(meeting_id)
            assert meeting is not None
            meeting.duration_seconds = result.duration_seconds
            meeting.language = result.language
            meeting.status = "analyzing"
            await session.commit()
        await self._record(meeting_id, "transcription", "succeeded")

        # Phase 4 — run the agent graph.
        async def recorder(stage: str, status: str, detail: str | None) -> None:
            await self._record(meeting_id, stage, status, detail)

        transcript_text = build_transcript_text(
            result.segments, display, self._settings.max_prompt_chars
        )
        if not result.segments:  # no diarization data at all — fall back to raw text
            transcript_text = result.raw_text[: self._settings.max_prompt_chars]

        graph = build_pipeline(recorder)
        state = await graph.ainvoke(
            {
                "meeting_context": f"Meeting: {title} | Date: {meeting_date.isoformat()}",
                "transcript_text": transcript_text,
                "talk_shares": compute_talk_shares(result.segments, display),
                "agent_errors": {},
            }
        )

        # Phase 5 — persist report + action items.
        async with self._factory() as session:
            ReportRepository(session).add(
                Report(
                    meeting_id=meeting_id,
                    executive_summary=state.get(
                        "executive_summary", "Summary unavailable for this meeting."
                    ),
                    topics=state.get("topics", []),
                    decisions=state.get("decisions", []),
                    risks=state.get("risks", []),
                    open_questions=state.get("open_questions", []),
                    deadlines=state.get("deadlines", []),
                    next_meeting_agenda=state.get("next_meeting_agenda", []),
                    health_score=state.get("health_score", 0),
                    health_breakdown=state.get("health_breakdown", {}),
                    agent_warnings=state.get("agent_errors", {}),
                    model=self._settings.gemini_agent_model,
                )
            )
            items = []
            for i, raw in enumerate(state.get("action_items", [])):
                due: date | None = None
                if raw.get("due_date"):
                    try:
                        due = date.fromisoformat(raw["due_date"])
                    except ValueError:
                        due = None
                priority = raw.get("priority", "medium")
                items.append(
                    ActionItem(
                        meeting_id=meeting_id,
                        task=raw["task"],
                        owner=raw.get("owner"),
                        due_date=due,
                        priority=priority if priority in ACTION_PRIORITIES else "medium",
                        sort_order=i,
                    )
                )
            ActionItemRepository(session).add_all(items)
            await session.commit()
        await self._record(meeting_id, "report", "succeeded")

        # Phase 6 — embeddings for RAG chat. Non-fatal: chat degrades, report survives.
        await self._record(meeting_id, "embeddings", "started")
        try:
            cleaned = state.get("cleaned_transcript", transcript_text)
            chunk_specs = build_chunks(result.segments, display) or [(cleaned, None, None)]
            vectors = await embed_texts([c[0] for c in chunk_specs])
            async with self._factory() as session:
                ChunkRepository(session).add_all(
                    [
                        TranscriptChunk(
                            meeting_id=meeting_id,
                            chunk_index=i,
                            content=content,
                            start_ms=start,
                            end_ms=end,
                            embedding=vec,
                        )
                        for i, ((content, start, end), vec) in enumerate(
                            zip(chunk_specs, vectors, strict=True)
                        )
                    ]
                )
                await session.commit()
            await self._record(meeting_id, "embeddings", "succeeded")
        except Exception as exc:
            log.warning("embeddings_failed", error=str(exc))
            await self._record(meeting_id, "embeddings", "failed", str(exc)[:500])

        # Phase 7 — done.
        await self._set_status(meeting_id, "completed")
        await self._record(meeting_id, "pipeline", "succeeded")
