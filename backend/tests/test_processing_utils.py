from app.services.processing import (
    build_chunks,
    build_transcript_text,
    compute_talk_shares,
    format_ms,
)
from app.transcription.base import SegmentIn


def seg(label: str, start: int, end: int, text: str) -> SegmentIn:
    return SegmentIn(speaker_label=label, start_ms=start, end_ms=end, text=text)


DISPLAY = {"S1": "Priya", "S2": "Rahul"}


def test_format_ms() -> None:
    assert format_ms(0) == "00:00"
    assert format_ms(61_000) == "01:01"
    assert format_ms(3_599_000) == "59:59"


def test_transcript_text_uses_display_names_and_timestamps() -> None:
    text = build_transcript_text(
        [seg("S1", 0, 2000, "Hello"), seg("S2", 2000, 5000, "Hi there")], DISPLAY, 10_000
    )
    assert text == "[00:00] Priya: Hello\n[00:02] Rahul: Hi there"


def test_transcript_text_truncates_at_cap() -> None:
    segments = [seg("S1", i * 1000, (i + 1) * 1000, "word " * 50) for i in range(100)]
    text = build_transcript_text(segments, DISPLAY, 500)
    assert len(text) < 600
    assert "truncated" in text


def test_talk_shares_sum_to_one() -> None:
    shares = compute_talk_shares(
        [seg("S1", 0, 3000, "a"), seg("S2", 3000, 4000, "b")], DISPLAY
    )
    assert shares == {"Priya": 0.75, "Rahul": 0.25}


def test_chunks_group_segments_and_keep_time_bounds() -> None:
    segments = [seg("S1", i * 1000, (i + 1) * 1000, "x" * 300) for i in range(10)]
    chunks = build_chunks(segments, DISPLAY, max_chars=1000)
    assert len(chunks) > 1
    content, start, end = chunks[0]
    assert start == 0
    assert end is not None and end > 0
    assert "Priya" in content
    # No chunk wildly exceeds the cap (one segment of overshoot is allowed).
    assert all(len(c[0]) < 1400 for c in chunks)
