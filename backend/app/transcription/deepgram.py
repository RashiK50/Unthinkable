"""Deepgram nova-3 — primary provider. Chosen because diarization is native,
which speaker analytics and the timeline depend on."""
import httpx

from app.core.config import Settings
from app.core.exceptions import UnprocessableAudioError
from app.transcription.base import SegmentIn, TranscriptResult

_API = "https://api.deepgram.com/v1/listen"
_PARAMS = {
    "model": "nova-3",
    "diarize": "true",
    "punctuate": "true",
    "smart_format": "true",
    "utterances": "true",
    "detect_language": "true",
}


class DeepgramProvider:
    def __init__(self, settings: Settings) -> None:
        self._key = settings.deepgram_api_key

    async def transcribe(self, audio_url: str) -> TranscriptResult:
        async with httpx.AsyncClient(timeout=httpx.Timeout(900, connect=30)) as client:
            resp = await client.post(
                _API,
                params=_PARAMS,
                headers={"Authorization": f"Token {self._key}"},
                json={"url": audio_url},
            )
        if resp.status_code >= 400:
            raise UnprocessableAudioError(f"Deepgram error: {resp.text[:500]}")
        data = resp.json()

        results = data.get("results", {})
        channels = results.get("channels", [])
        if not channels or not channels[0].get("alternatives"):
            raise UnprocessableAudioError("Deepgram returned no transcription")
        alt = channels[0]["alternatives"][0]
        raw_text = alt.get("transcript", "").strip()
        if not raw_text:
            raise UnprocessableAudioError("No speech detected in audio")

        segments = [
            SegmentIn(
                speaker_label=f"S{int(utt.get('speaker', 0)) + 1}",
                start_ms=int(float(utt["start"]) * 1000),
                end_ms=int(float(utt["end"]) * 1000),
                text=utt.get("transcript", "").strip(),
            )
            for utt in results.get("utterances", [])
            if utt.get("transcript", "").strip()
        ]

        metadata = data.get("metadata", {})
        duration = metadata.get("duration")
        language = channels[0].get("detected_language")
        return TranscriptResult(
            raw_text=raw_text,
            provider="deepgram",
            language=language,
            duration_seconds=int(duration) if duration else None,
            segments=segments,
        )
