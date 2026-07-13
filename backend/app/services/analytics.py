"""Speaker analytics — a pure function of transcript_segments, computed on demand
(API design doc: no second source of truth to keep in sync)."""
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.core.security import AuthUser
from app.models.transcript import TranscriptSegment
from app.repositories.meetings import MeetingRepository
from app.repositories.reports import ReportRepository
from app.repositories.transcripts import TranscriptRepository
from app.schemas.report import AnalyticsOut, SpeakerStat, TopicSpeakerRow


def _overlap_ms(seg: TranscriptSegment, start: int, end: int) -> int:
    return max(0, min(seg.end_ms, end) - max(seg.start_ms, start))


class AnalyticsService:
    def __init__(
        self,
        meetings: MeetingRepository,
        transcripts: TranscriptRepository,
        reports: ReportRepository,
    ) -> None:
        self._meetings = meetings
        self._transcripts = transcripts
        self._reports = reports

    async def compute(self, user: AuthUser, meeting_id: UUID) -> AnalyticsOut:
        if await self._meetings.get_owned(meeting_id, user.id) is None:
            raise NotFoundError("Meeting not found")

        segments = await self._transcripts.get_segments(meeting_id)
        speakers = await self._transcripts.get_speakers(meeting_id)
        display = {s.label: s.display_name for s in speakers}

        talk: dict[str, int] = {}
        counts: dict[str, int] = {}
        for seg in segments:
            talk[seg.speaker_label] = talk.get(seg.speaker_label, 0) + max(
                0, seg.end_ms - seg.start_ms
            )
            counts[seg.speaker_label] = counts.get(seg.speaker_label, 0) + 1
        total = sum(talk.values()) or 1

        stats = sorted(
            (
                SpeakerStat(
                    label=label,
                    display_name=display.get(label, label),
                    talk_time_ms=ms,
                    contribution_count=counts.get(label, 0),
                    share=round(ms / total, 4),
                )
                for label, ms in talk.items()
            ),
            key=lambda s: s.talk_time_ms,
            reverse=True,
        )

        rows: list[TopicSpeakerRow] = []
        report = await self._reports.get(meeting_id)
        if report is not None:
            for topic in report.topics:
                start, end = topic.get("start_ms"), topic.get("end_ms")
                if start is None or end is None or end <= start:
                    continue
                per_speaker: dict[str, int] = {}
                for seg in segments:
                    ms = _overlap_ms(seg, start, end)
                    if ms > 0:
                        name = display.get(seg.speaker_label, seg.speaker_label)
                        per_speaker[name] = per_speaker.get(name, 0) + ms
                if per_speaker:
                    title = topic.get("title", "?")
                    rows.append(TopicSpeakerRow(topic=title, speakers=per_speaker))

        return AnalyticsOut(speakers=stats, topics_by_speaker=rows)
