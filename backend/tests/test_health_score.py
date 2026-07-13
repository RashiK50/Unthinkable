"""The health rubric is deterministic on purpose — so it gets exact-value tests."""
from app.ai.health import compute_health


def _items(n_owned: int, n_dated: int, total: int) -> list[dict]:
    items = []
    for i in range(total):
        items.append(
            {
                "task": f"t{i}",
                "owner": "Rahul" if i < n_owned else None,
                "due_date": "2026-08-01" if i < n_dated else None,
            }
        )
    return items


def test_perfect_meeting_scores_high() -> None:
    score, breakdown = compute_health(
        decisions=[{"decision": "ship it"}] * 3,
        open_questions=[],
        action_items=_items(4, 4, 4),
        risks=[],
        talk_shares={"A": 0.5, "B": 0.5},
    )
    assert score >= 90
    assert breakdown["ownership"]["score"] == 100
    assert breakdown["deadlines"]["score"] == 100
    assert breakdown["clarity"]["score"] == 100


def test_unowned_undated_items_drag_score() -> None:
    score, breakdown = compute_health(
        decisions=[],
        open_questions=[{"question": "?"}] * 4,
        action_items=_items(0, 0, 4),
        risks=[],
        talk_shares={"A": 0.5, "B": 0.5},
    )
    assert breakdown["ownership"]["score"] == 0
    assert breakdown["deadlines"]["score"] == 0
    assert breakdown["clarity"]["score"] == 0
    assert score < 40


def test_monologue_penalized() -> None:
    _, breakdown = compute_health(
        decisions=[], open_questions=[], action_items=[], risks=[], talk_shares={"A": 1.0}
    )
    assert breakdown["participation"]["score"] == 40


def test_high_severity_blockers_hit_resolution() -> None:
    _, breakdown = compute_health(
        decisions=[],
        open_questions=[],
        action_items=[],
        risks=[{"kind": "blocker", "severity": "high"}] * 2,
        talk_shares={"A": 0.5, "B": 0.5},
    )
    assert breakdown["resolution"]["score"] == 20  # 100 - 2 * (20 * 2)


def test_score_always_in_bounds() -> None:
    score, _ = compute_health(
        decisions=[],
        open_questions=[],
        action_items=[],
        risks=[{"kind": "blocker", "severity": "high"}] * 20,
        talk_shares={},
    )
    assert 0 <= score <= 100
