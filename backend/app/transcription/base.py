"""Transcription provider boundary (strategy pattern).

New providers implement `TranscriptionProvider` and register in `get_provider` —
nothing else in the codebase changes (Open/Closed in practice).
"""
from dataclasses import dataclass, field
from typing import Protocol

from app.core.config import Settings


@dataclass(frozen=True)
class SegmentIn:
    speaker_label: str
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True)
class TranscriptResult:
    raw_text: str
    provider: str
    language: str | None = None
    duration_seconds: int | None = None
    segments: list[SegmentIn] = field(default_factory=list)


class TranscriptionProvider(Protocol):
    async def transcribe(self, audio_url: str) -> TranscriptResult: ...


def get_provider(settings: Settings) -> TranscriptionProvider:
    from app.transcription.deepgram import DeepgramProvider
    from app.transcription.whisper import WhisperProvider

    match settings.transcription_provider:
        case "deepgram":
            return DeepgramProvider(settings)
        case "whisper":
            return WhisperProvider(settings)
        case other:
            raise ValueError(f"Unknown transcription provider: {other}")
