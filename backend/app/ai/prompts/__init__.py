"""Prompt templates, versioned as code. Each agent gets a focused prompt —
the whole point of the multi-agent split (architecture doc §2.6)."""


def clean_prompt(context: str, transcript: str) -> str:
    return f"""You are the transcript-cleaning stage of a meeting intelligence pipeline.
{context}

Clean the transcript below: fix obvious transcription errors, remove filler words
(um, uh, you know), fix punctuation and casing. PRESERVE the speaker attributions and
[MM:SS] timestamps exactly as they appear. Do NOT summarize, do NOT drop content.

TRANSCRIPT:
{transcript}"""


def topics_prompt(context: str, cleaned: str) -> str:
    return f"""You are the topic-detection stage of a meeting intelligence pipeline.
{context}

Identify the 3-8 key discussion topics in order. For each: a short title, a 1-2 sentence
summary, and approximate start_ms/end_ms derived from the [MM:SS] timestamps
(MM:SS -> milliseconds). Only include topics genuinely discussed.

TRANSCRIPT:
{cleaned}"""


def decisions_prompt(context: str, cleaned: str) -> str:
    return f"""You are the decision-extraction stage of a meeting intelligence pipeline.
{context}

Extract:
1. decisions - things the group explicitly settled ("we will X"). Include brief context
   and who made or announced the decision if identifiable from speaker attributions.
2. open_questions - questions raised but NOT resolved by the end of the meeting.

Be strict: a proposal that was not agreed on is an open question, not a decision.
Empty lists are valid answers.

TRANSCRIPT:
{cleaned}"""


def actions_prompt(context: str, cleaned: str) -> str:
    return f"""You are the action-item extraction stage of a meeting intelligence pipeline.
{context}

Extract concrete action items: task (imperative phrasing), owner (the speaker/person who
took it, if stated), due_date (ISO YYYY-MM-DD only if a date is stated or clearly inferable
from the meeting date; otherwise null), priority (low|medium|high|urgent based on urgency
language). Do not invent owners or dates. Empty list is a valid answer.

TRANSCRIPT:
{cleaned}"""


def risks_prompt(context: str, cleaned: str) -> str:
    return f"""You are the risk-detection stage of a meeting intelligence pipeline.
{context}

Extract risks and blockers mentioned or clearly implied:
- kind "blocker": something actively preventing progress now.
- kind "risk": something that could cause problems later.
Assign severity low|medium|high. Empty list is a valid answer.

TRANSCRIPT:
{cleaned}"""


def deadlines_prompt(context: str, cleaned: str) -> str:
    return f"""You are the deadline-extraction stage of a meeting intelligence pipeline.
{context}

Extract every deadline or time commitment mentioned: item (what is due), date_text (the
exact phrase used, e.g. "end of next week"), date_normalized (ISO YYYY-MM-DD resolved
against the meeting date, or null when genuinely ambiguous).

TRANSCRIPT:
{cleaned}"""


def summary_prompt(context: str, cleaned: str, extracted: str) -> str:
    return f"""You are the executive-summary stage of a meeting intelligence pipeline.
{context}

Already-extracted structured findings (use them for consistency, do not contradict them):
{extracted}

Write:
1. executive_summary - 4-8 sentences a director could read instead of attending:
   what the meeting was about, what was concluded, what happens next.
2. next_meeting_agenda - 3-6 concrete agenda bullets for the follow-up meeting,
   driven by the open questions and unfinished threads.

TRANSCRIPT:
{cleaned}"""


def email_prompt(tone: str, meeting_title: str, report_block: str) -> str:
    return f"""Write a follow-up email for the meeting "{meeting_title}", in a {tone} tone.

Use this meeting report:
{report_block}

Rules: subject line under 80 chars; body opens with a 1-2 sentence recap, then sections for
decisions, action items (with owners and deadlines), and open questions; closes by asking
recipients to flag corrections. Plain text, no markdown syntax. Sign off as "MeetIQ" on
behalf of the organizer."""


def chat_prompt(question: str, excerpts: str) -> str:
    return f"""You answer questions about ONE meeting using only the transcript excerpts below.
Each excerpt carries a hidden label like [chunk <id> | <start>-<end>] — this is internal
metadata for retrieval only.

Rules:
- Answer from the excerpts only. If they don't contain the answer, say the meeting doesn't
  appear to cover it - never guess.
- Quote or paraphrase specific speakers when relevant.
- Be concise and direct.
- NEVER mention chunk numbers, chunk ids, timestamps, or the [chunk ...] labels in your
  answer. Write natural prose as if speaking to the user — the interface shows sources
  separately, so citing them in text is redundant.

EXCERPTS:
{excerpts}

QUESTION: {question}"""
