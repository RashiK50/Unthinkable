"""Meeting health score — deliberately deterministic, not an LLM call.

Scores must be comparable across meetings; an LLM would drift. The rubric is a pure
function of the extraction agents' outputs, so every dimension can show its work
(the `rationale` the UI renders).
"""
from typing import Any

WEIGHTS = {
    "ownership": 0.25,
    "deadlines": 0.20,
    "clarity": 0.25,
    "resolution": 0.15,
    "participation": 0.15,
}


def _clamp(v: float) -> int:
    return int(max(0, min(100, round(v))))


def compute_health(
    decisions: list[dict[str, Any]],
    open_questions: list[dict[str, Any]],
    action_items: list[dict[str, Any]],
    risks: list[dict[str, Any]],
    talk_shares: dict[str, float],
) -> tuple[int, dict[str, Any]]:
    breakdown: dict[str, Any] = {}

    # Ownership: do action items have owners?
    if action_items:
        owned = sum(1 for a in action_items if a.get("owner"))
        score = _clamp(100 * owned / len(action_items))
        rationale = f"{owned} of {len(action_items)} action items have an owner"
    else:
        score, rationale = 50, "No action items captured — nothing was assigned"
    breakdown["ownership"] = {"score": score, "rationale": rationale}

    # Deadlines: do action items have due dates?
    if action_items:
        dated = sum(1 for a in action_items if a.get("due_date"))
        score = _clamp(100 * dated / len(action_items))
        rationale = f"{dated} of {len(action_items)} action items have a deadline"
    else:
        score, rationale = 50, "No action items to attach deadlines to"
    breakdown["deadlines"] = {"score": score, "rationale": rationale}

    # Clarity: decided vs. left open.
    total = len(decisions) + len(open_questions)
    if total:
        score = _clamp(100 * len(decisions) / total)
        rationale = f"{len(decisions)} decisions vs {len(open_questions)} unresolved questions"
    else:
        score, rationale = 60, "No explicit decisions or open questions detected"
    breakdown["clarity"] = {"score": score, "rationale": rationale}

    # Resolution: penalize live blockers and high-severity risks.
    penalty = 0
    for r in risks:
        is_blocker = r.get("kind") == "blocker"
        sev = r.get("severity", "medium")
        penalty += {"low": 5, "medium": 10, "high": 20}.get(sev, 10) * (2 if is_blocker else 1)
    score = _clamp(100 - penalty)
    rationale = f"{len(risks)} risks/blockers weighed by severity" if risks else "No risks raised"
    breakdown["resolution"] = {"score": score, "rationale": rationale}

    # Participation: balance of talk time.
    if len(talk_shares) <= 1:
        score, rationale = 40, "Single speaker — monologue, not a discussion"
    else:
        max_share = max(talk_shares.values())
        ideal = 1 / len(talk_shares)
        score = _clamp(100 - (max_share - ideal) * 150)
        rationale = f"Dominant speaker held {round(max_share * 100)}% of talk time"
    breakdown["participation"] = {"score": score, "rationale": rationale}

    overall = _clamp(sum(breakdown[d]["score"] * w for d, w in WEIGHTS.items()))
    return overall, breakdown
