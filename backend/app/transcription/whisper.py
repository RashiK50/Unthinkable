"""OpenAI Whisper fallback. Documented limitation: no diarization —
every segment is attributed to speaker 'S1'."""
import tempfile
from pathlib import Path

import httpx

from app.core.config import Settings
from app.core.exceptions import UnprocessableAudioError
from app.transcription.base import SegmentIn, TranscriptResult

_API = "https://api.openai.com/v1/audio/transcriptions"


class WhisperProvider:
    def __init__(self, settings: Settings) -> None:
        self._key = settings.openai_api_key

    async def transcribe(self, audio_url: str) -> TranscriptResult:
        # Whisper requires multipart bytes, so we stream the signed URL to a temp file.
        with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(900, connect=30)) as client:
                async with client.stream("GET", audio_url) as resp:
                    resp.raise_for_status()
                    with tmp_path.open("wb") as fh:
                        async for chunk in resp.aiter_bytes():
                            fh.write(chunk)

                with tmp_path.open("rb") as fh:
                    api_resp = await client.post(
                        _API,
                        headers={"Authorization": f"Bearer {self._key}"},
                        data={"model": "whisper-1", "response_format": "verbose_json"},
                        files={"file": ("audio.mp3", fh, "application/octet-stream")},
                    )
        finally:
            tmp_path.unlink(missing_ok=True)

        if api_resp.status_code >= 400:
            raise UnprocessableAudioError(f"Whisper error: {api_resp.text[:500]}")
        data = api_resp.json()
        raw_text = (data.get("text") or "").strip()
        if not raw_text:
            raise UnprocessableAudioError("No speech detected in audio")

        segments = [
            SegmentIn(
                speaker_label="S1",
                start_ms=int(float(seg["start"]) * 1000),
                end_ms=int(float(seg["end"]) * 1000),
                text=(seg.get("text") or "").strip(),
            )
            for seg in data.get("segments", [])
            if (seg.get("text") or "").strip()
        ]
        duration = data.get("duration")
        return TranscriptResult(
            raw_text=raw_text,
            provider="whisper",
            language=data.get("language"),
            duration_seconds=int(duration) if duration else None,
            segments=segments,
        )
