# MeetIQ — 5-Minute Demo Script

> Audience: reviewing engineer. Goal: show product depth first, engineering depth second.
> Prep: one processed meeting already in the account; a second short recording (~5 min mp3)
> ready to upload; backend `/docs` open in a spare tab.

## 0:00 — Framing (one sentence)

> "The assignment was a meeting summarizer — I built a meeting *intelligence* platform:
> multi-agent pipeline, health scoring, RAG chat, and action-item tracking, deployed on
> Vercel and Render with Supabase."

## 0:15 — Login + Dashboard

- Sign in → dashboard: stat cards (meetings, hours processed, open/overdue action items,
  average health), **AI insights** ("3 action items overdue, all owned by Rahul").
- Point out: insights are deterministic aggregation over stored reports — no extra LLM
  spend, always explainable.

## 0:45 — Upload flow

- Upload the second recording: drag & drop, title autofill, live progress bar.
- **Say the architecture out loud:** "The file goes browser → Supabase Storage on a signed
  URL — it never touches my API. The API returns 202 and the pipeline runs async; that
  stage tracker is polling a status endpoint fed by an events table."
- Show the stage tracker ticking: Transcribe → Clean → five extraction agents → Health →
  Summary. Mention the extractors run **in parallel** in LangGraph.
- Don't wait for it — switch to the pre-processed meeting.

## 1:45 — The intelligence report

- Overview tab: executive summary, decisions (with who made them), risks with severity,
  open questions, deadlines, suggested next-meeting agenda.
- **Health score**: open the breakdown. "This is deliberately *not* an LLM — it's a
  deterministic rubric over the extracted data, so scores are comparable across meetings,
  and every dimension shows its work."

## 2:30 — Transcript & speakers

- Timeline strip: topic-colored, click a topic → jumps to that point in the transcript.
- Diarized segments; rename "Speaker 1" → "Priya" inline.

## 3:00 — Action items

- Editable table: flip a status, set a deadline, add a manual item. "AI-extracted items are
  rows, not report text — they have their own lifecycle after the meeting."

## 3:30 — Chat (the wow moment)

- Ask: "Who owns deployment?" then "Was budget discussed?"
- Point at the timestamp chips: "This is RAG over pgvector — chunks embedded at pipeline
  time, answers cite transcript locations, and it refuses to answer beyond the transcript."

## 4:15 — Follow-up email + export

- Generate follow-up email (friendly tone), copy to clipboard.
- Export the PDF; open it. "Same template renders screen, Markdown, text, and PDF."

## 4:45 — Engineering close

- Flash `/docs` (OpenAPI): versioned API, one error envelope.
- One sentence each: layered backend (router→service→repo, DI, fakes in tests), RLS on
  every table + user-scoped queries, transcription behind a provider interface, tradeoffs
  documented in the README ("in-process runner today, Celery seam already in place").

> Closing line: "Everything here is the boring-but-correct version of each decision, with
> the upgrade path written down — that's what I'd want to maintain six months from now."
