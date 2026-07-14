# MeetIQ — AI Meeting Intelligence Platform

> Transform meetings into structured business intelligence.

Upload a meeting recording; MeetIQ transcribes it (with speaker diarization), runs a
multi-agent LangGraph pipeline over the transcript, and produces an intelligence report:
executive summary, key topics, decisions, action items, risks & blockers, open questions,
deadlines, a suggested next-meeting agenda, and a 0–100 **meeting health score** with a
per-dimension breakdown. Then you can **chat with the meeting** (RAG over pgvector, answers
cite transcript timestamps), track action items, view speaker analytics, generate a
follow-up email, and export to PDF / Markdown / text.

## Architecture

```
React SPA (Vercel) ──JWT──▶ FastAPI (Render, Docker) ──▶ Supabase Postgres (+pgvector)
        │                        │        │
        │ signed upload          │        └─▶ Gemini (agents, embeddings, chat)
        ▼                        ▼
  Supabase Storage ◀──signed download── Deepgram / Whisper (transcription)
```

- **Uploads go browser → Supabase Storage directly** via signed URLs; audio bytes never
  pass through the API.
- **Processing is asynchronous**: `POST /process` returns `202`; every stage transition is
  written to Postgres; the UI polls a status endpoint.
- **AI pipeline** (LangGraph): Cleaning → *(parallel)* Topics + Decisions + Action Items +
  Risks + Deadlines → Health (deterministic rubric, not an LLM) → Summary → persist.
  Extraction failures degrade gracefully instead of failing the meeting.
- **Layered backend**: routers → services → repositories, dependency-injected; the only
  module importing the Gemini SDK is `app/ai/llm.py`.

Full design docs: [`docs/01-architecture.md`](docs/01-architecture.md) ·
[`docs/02-folder-structure.md`](docs/02-folder-structure.md) ·
[`docs/03-api-design.md`](docs/03-api-design.md) ·
[`docs/04-wireframes.md`](docs/04-wireframes.md)

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React 18 + Vite + TypeScript (strict), TailwindCSS, TanStack Query, Recharts |
| Backend | FastAPI, SQLAlchemy 2 (async), Pydantic v2, structlog |
| AI | LangGraph orchestration, Gemini 2.5 Flash (agents), Gemini embeddings → 768-dim (RAG) |
| Transcription | Deepgram nova-3 (diarization) with Whisper fallback, behind a provider interface |
| Data | Supabase: Postgres + pgvector, Auth (JWT), Storage — RLS on every table |
| Deploy | Vercel (frontend), Render via Docker (backend, WeasyPrint PDF export) |

## Getting started

### 1. Supabase

1. Create a project at [supabase.com](https://supabase.com).
2. Run [`database/schema.sql`](database/schema.sql) in the SQL editor (creates tables,
   enums, RLS policies, the private `meeting-audio` bucket, and storage policies).
3. Collect: project URL, anon key, service-role key, JWT secret, and the connection-pooler
   database URI. The **JWT secret** (Project Settings → API → JWT Secret, legacy HS256) is
   what the backend uses to verify tokens — it must be set correctly or every request 401s.

### 2. Backend

```bash
cd backend
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env                            # fill in every value
uvicorn app.main:app --reload                   # http://localhost:8000/docs
```

> **Gemini quota note:** the pipeline makes ~7 model calls per meeting (cleaning + 5
> extractors + summary). The free tier allows only 5 requests/minute, so the backend
> retries on `429` with backoff — a free-tier run just takes longer. For snappy processing,
> enable billing on your Gemini key; no code change needed.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env                            # fill in every value
npm run dev                                     # http://localhost:5173
```

### 4. Tests

```bash
cd backend && pytest            # unit tests: health rubric, pipeline utils, services, exports
cd frontend && npm test         # vitest
# e2e (needs a running stack): see tests/README.md
```

## Deployment

- **Backend**: push to GitHub, create a Render *Blueprint* from `render.yaml`, fill the
  `sync: false` env vars in the dashboard. Docker is required — WeasyPrint's native
  libraries ship in the image.
- **Frontend**: import the repo in Vercel with root directory `frontend/`; set
  `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL` (the Render URL).
  `vercel.json` handles the SPA rewrite.
- Set the backend's `FRONTEND_ORIGIN` to the Vercel URL (CORS).

## Security model

- Supabase Auth issues JWTs; FastAPI verifies them per-request. The API never sees passwords.
- Every query is user-scoped at the repository layer **and** RLS is enabled on every table
  as defense-in-depth. Foreign resource IDs return 404, never 403.
- Storage bucket is private; object keys are `{user_id}/{meeting_id}/{file}` and storage
  policies enforce folder ownership. All access is via short-lived signed URLs.
- All secrets are environment variables, validated at boot.

## Known tradeoffs (deliberate, documented)

| Now | Later |
|---|---|
| In-process asyncio pipeline runner | Celery/Arq behind the existing `PipelineDispatcher` seam |
| Status polling every ~2.5s | Supabase Realtime on `processing_events` |
| Report text keeps original speaker labels after rename | Re-render report references on rename |
| Single Gemini provider | LLM factory already isolates the SDK |
| Free-tier rate limits handled by per-call `429` backoff (slower runs) | Paid Gemini tier, or a token-bucket throttle across agents |

## Demo

See [`docs/05-demo-script.md`](docs/05-demo-script.md) for a 5-minute walkthrough script.
