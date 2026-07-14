"""LangGraph pipeline: Cleaning -> five parallel extraction agents -> Health -> Summary.

Fan-out is the one deliberate improvement over a linear chain: the extractors have no
data dependency on each other, so they run concurrently. Extraction failures degrade
gracefully (recorded in agent_errors, section rendered empty); only cleaning falls back
to the raw transcript.
"""
import json
import operator
from collections.abc import Awaitable, Callable
from typing import Annotated, Any, TypedDict
import traceback    

import structlog
from langgraph.graph import END, START, StateGraph

from app.ai import llm, prompts
from app.ai.health import compute_health
from app.ai.outputs import (
    ActionItemList,
    CleanedTranscript,
    DeadlineList,
    DecisionResult,
    RiskList,
    SummaryResult,
    TopicList,
)
from app.core.config import get_settings

logger = structlog.get_logger()

EventRecorder = Callable[[str, str, str | None], Awaitable[None]]

EXTRACTORS = ["topics", "decisions", "action_items", "risks", "deadlines"]


class PipelineState(TypedDict, total=False):
    meeting_context: str  # "Meeting: <title> · Date: <iso>"
    transcript_text: str  # speaker-attributed, [MM:SS]-timestamped
    talk_shares: dict[str, float]
    cleaned_transcript: str
    topics: list[dict[str, Any]]
    decisions: list[dict[str, Any]]
    open_questions: list[dict[str, Any]]
    action_items: list[dict[str, Any]]
    risks: list[dict[str, Any]]
    deadlines: list[dict[str, Any]]
    health_score: int
    health_breakdown: dict[str, Any]
    executive_summary: str
    next_meeting_agenda: list[str]
    agent_errors: Annotated[dict[str, str], operator.or_]


NodeFn = Callable[[PipelineState], Awaitable[dict[str, Any]]]


import traceback

def _wrap(name: str, fn: NodeFn, recorder: EventRecorder, fallback: NodeFn | None = None) -> NodeFn:
    """Uniform node behavior: events around execution, errors captured not raised."""

    async def node(state: PipelineState) -> dict[str, Any]:
        await recorder(name, "started", None)

        try:
            result = await fn(state)
            await recorder(name, "succeeded", None)
            return result

        except Exception as exc:  # degrade, don't fail the meeting
            print("\n" + "=" * 80)
            print(f"FAILED AGENT: {name}")
            print("=" * 80)
            traceback.print_exc()
            print("=" * 80 + "\n")

            logger.exception("agent_failed", agent=name)

            await recorder(name, "failed", str(exc)[:500])

            result = await fallback(state) if fallback else {}

            return {
                **result,
                "agent_errors": {
                    name: str(exc)[:500]
                },
            }

    return node


async def _clean(state: PipelineState) -> dict[str, Any]:
    out = await llm.generate_structured(
        prompts.clean_prompt(state["meeting_context"], state["transcript_text"]),
        CleanedTranscript,
    )
    return {"cleaned_transcript": out.cleaned_text}


async def _topics(state: PipelineState) -> dict[str, Any]:
    out = await llm.generate_structured(
        prompts.topics_prompt(state["meeting_context"], state["cleaned_transcript"]), TopicList
    )
    return {"topics": [t.model_dump() for t in out.topics]}


async def _decisions(state: PipelineState) -> dict[str, Any]:
    out = await llm.generate_structured(
        prompts.decisions_prompt(state["meeting_context"], state["cleaned_transcript"]),
        DecisionResult,
    )
    return {
        "decisions": [d.model_dump() for d in out.decisions],
        "open_questions": [q.model_dump() for q in out.open_questions],
    }


async def _action_items(state: PipelineState) -> dict[str, Any]:
    out = await llm.generate_structured(
        prompts.actions_prompt(state["meeting_context"], state["cleaned_transcript"]),
        ActionItemList,
    )
    return {"action_items": [a.model_dump() for a in out.action_items]}


async def _risks(state: PipelineState) -> dict[str, Any]:
    out = await llm.generate_structured(
        prompts.risks_prompt(state["meeting_context"], state["cleaned_transcript"]), RiskList
    )
    return {"risks": [r.model_dump() for r in out.risks]}


async def _deadlines(state: PipelineState) -> dict[str, Any]:
    out = await llm.generate_structured(
        prompts.deadlines_prompt(state["meeting_context"], state["cleaned_transcript"]),
        DeadlineList,
    )
    return {"deadlines": [d.model_dump() for d in out.deadlines]}


async def _health(state: PipelineState) -> dict[str, Any]:
    score, breakdown = compute_health(
        decisions=state.get("decisions", []),
        open_questions=state.get("open_questions", []),
        action_items=state.get("action_items", []),
        risks=state.get("risks", []),
        talk_shares=state.get("talk_shares", {}),
    )
    return {"health_score": score, "health_breakdown": breakdown}


async def _summary(state: PipelineState) -> dict[str, Any]:
    extracted = json.dumps(
        {
            "topics": state.get("topics", []),
            "decisions": state.get("decisions", []),
            "open_questions": state.get("open_questions", []),
            "action_items": state.get("action_items", []),
            "risks": state.get("risks", []),
            "deadlines": state.get("deadlines", []),
        },
        indent=1,
    )
    out = await llm.generate_structured(
        prompts.summary_prompt(state["meeting_context"], state["cleaned_transcript"], extracted),
        SummaryResult,
        model=get_settings().gemini_summary_model,
    )
    return {
        "executive_summary": out.executive_summary,
        "next_meeting_agenda": out.next_meeting_agenda,
    }


async def _clean_fallback(state: PipelineState) -> dict[str, Any]:
    return {"cleaned_transcript": state["transcript_text"]}


async def _summary_fallback(state: PipelineState) -> dict[str, Any]:
    return {"executive_summary": "Summary unavailable for this meeting.", "next_meeting_agenda": []}


def build_pipeline(recorder: EventRecorder):
    g: StateGraph = StateGraph(PipelineState)
    g.add_node("cleaning", _wrap("cleaning", _clean, recorder, fallback=_clean_fallback))
    g.add_node("topics", _wrap("topics", _topics, recorder))
    g.add_node("decisions", _wrap("decisions", _decisions, recorder))
    g.add_node("action_items", _wrap("action_items", _action_items, recorder))
    g.add_node("risks", _wrap("risks", _risks, recorder))
    g.add_node("deadlines", _wrap("deadlines", _deadlines, recorder))
    g.add_node("health", _wrap("health", _health, recorder))
    g.add_node("summary", _wrap("summary", _summary, recorder, fallback=_summary_fallback))

    g.add_edge(START, "cleaning")
    for name in EXTRACTORS:
        g.add_edge("cleaning", name)
    g.add_edge(EXTRACTORS, "health")  # join: waits for all five extractors
    g.add_edge("health", "summary")
    g.add_edge("summary", END)
    return g.compile()
