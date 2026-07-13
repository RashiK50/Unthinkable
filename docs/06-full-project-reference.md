# MeetIQ — Full Project Reference

> **Purpose of this document**: a single, self-contained technical reference to the entire
> MeetIQ codebase — every file, what it contains, how the pieces connect, and how data flows
> end to end. Written so that another AI/engineer with zero prior context can read this one
> file and understand the whole system without exploring the repo. If anything here conflicts
> with the code, the code wins — this is a snapshot, kept for orientation, not a spec to
> enforce.

---

## 1. What MeetIQ is

MeetIQ is an AI meeting-intelligence SaaS. A user uploads a meeting recording (mp3/wav/mp4/m4a).
The system transcribes it with speaker diarization, runs a multi-agent LangGraph pipeline over
the transcript, and produces a structured intelligence report: executive summary, key topics,
decisions, action items (owner/deadline/priority/status), risks & blockers, open questions,
deadlines, a suggested next-meeting agenda, and a deterministic 0–100 health score with a
per-dimension breakdown. Users can also: chat with the transcript (RAG over pgvector, answers
cite timestamps), view speaker analytics (talk time, contributions, topic-by-speaker), generate
a follow-up email draft, and export the report as PDF/Markdown/plain text.

It was built to exceed a basic "meeting summarizer" assignment — the differentiators are the
multi-agent pipeline (not one big prompt), the deterministic health score, RAG chat with
citations, and production engineering practices (layered architecture, RLS, typed contracts,
tests, deployment configs).

---

## 2. Tech stack (exact choices and why)

| Concern | Choice | Why |
|---|---|---|
| Frontend | React 18 + Vite + TypeScript (strict) | SPA is right because there's no SEO need (auth-gated dashboard) |
| Styling | TailwindCSS, dark-first, shadcn-style hand-built primitives | No component library dependency; full control |
| Data fetching | TanStack Query | Caching, polling (`refetchInterval`), mutations |
| Charts | Recharts | Speaker talk-time pie, contributions bar |
| Backend | FastAPI (Python 3.12) | Async, typed, OpenAPI for free |
| ORM | SQLAlchemy 2 async + asyncpg | Typed queries; schema itself is NOT owned by the ORM |
| Validation | Pydantic v2 | Request/response schemas, also Gemini structured-output schemas |
| Auth | Supabase Auth (JWT) | Backend only verifies tokens, never sees passwords |
| Database | Supabase Postgres + pgvector extension | RLS, storage, and vector search all in one managed service |
| AI orchestration | LangGraph | Multi-agent graph with fan-out/fan-in |
| LLM | Google Gemini (`gemini-2.5-flash` default) | Structured JSON output via `response_schema` |
| Embeddings | Gemini `text-embedding-004` (768-dim) | Used for RAG chat over transcript chunks |
| Transcription | Deepgram nova-3 (primary, diarization) / OpenAI Whisper (fallback, no diarization) | Provider abstraction, swappable |
| PDF export | WeasyPrint (needs native libs → Docker) | One HTML/Markdown template renders to 3 formats |
| Deployment | Vercel (frontend), Render via Dockerfile (backend) | render.yaml blueprint checked in |
| Structured logging | structlog | JSON in prod, console in dev |

---

## 3. Repository layout (every file, top to bottom)

```
meeting_summarizer/                      <- repo root, git-initialized, branch "main"
├── .gitignore
├── README.md                            <- setup, deploy, security model, tradeoffs
├── render.yaml                          <- Render blueprint for backend Docker deploy
│
├── docs/                                <- design docs (Phase 1 deliverables + this file)
│   ├── 01-architecture.md               <- system diagram, 9 key decisions, tradeoffs table
│   ├── 02-folder-structure.md           <- monorepo layout rationale
│   ├── 03-api-design.md                 <- every endpoint, request/response examples
│   ├── 04-wireframes.md                 <- design tokens + ASCII wireframes per screen
│   ├── 05-demo-script.md                <- 5-minute walkthrough script
│   └── 06-full-project-reference.md     <- THIS FILE
│
├── database/
│   ├── schema.sql                       <- canonical Postgres schema (tables, enums, RLS, storage)
│   └── migrations/README.md             <- how to apply schema.sql via Supabase CLI
│
├── backend/                             <- FastAPI app, deployed to Render as Docker
│   ├── Dockerfile
│   ├── pyproject.toml                   <- deps, ruff/mypy/pytest config
│   ├── .env.example
│   ├── app/
│   │   ├── main.py                      <- FastAPI app factory, CORS, routers, /healthz
│   │   ├── core/
│   │   │   ├── config.py                <- Settings (pydantic-settings), get_settings()
│   │   │   ├── exceptions.py            <- AppError hierarchy + one JSON error envelope
│   │   │   ├── logging.py               <- structlog configuration
│   │   │   └── security.py              <- Supabase JWT verify -> AuthUser
│   │   ├── db/
│   │   │   └── session.py               <- async engine/session factory, get_session()
│   │   ├── models/                      <- SQLAlchemy ORM models (typed queries only, not schema owner)
│   │   │   ├── base.py
│   │   │   ├── meeting.py
│   │   │   ├── transcript.py            <- Transcript, TranscriptSegment, Speaker, TranscriptChunk
│   │   │   ├── report.py
│   │   │   ├── action_item.py
│   │   │   ├── chat.py
│   │   │   └── event.py                 <- ProcessingEvent
│   │   ├── schemas/                     <- Pydantic request/response contracts
│   │   │   ├── common.py                <- Page[T]
│   │   │   ├── meeting.py
│   │   │   ├── transcript.py
│   │   │   ├── report.py                <- ReportOut, AnalyticsOut, EmailDraft
│   │   │   ├── action_item.py
│   │   │   ├── chat.py
│   │   │   └── dashboard.py
│   │   ├── repositories/                <- ALL SQL lives here, one class per aggregate
│   │   │   ├── meetings.py
│   │   │   ├── transcripts.py
│   │   │   ├── reports.py
│   │   │   ├── action_items.py
│   │   │   ├── chat.py
│   │   │   ├── chunks.py                <- pgvector cosine search
│   │   │   └── events.py
│   │   ├── services/                    <- business logic / use-cases, orchestrates repos
│   │   │   ├── meetings.py              <- MeetingService: create/detail/status/rename/delete
│   │   │   ├── processing.py            <- ProcessingService: THE pipeline runner
│   │   │   ├── storage.py               <- StorageClient: Supabase Storage signed URLs
│   │   │   ├── chat.py                  <- ChatService: RAG ask/history
│   │   │   ├── analytics.py             <- AnalyticsService: speaker stats (computed, not stored)
│   │   │   ├── exports.py               <- ExportService: markdown/txt/pdf rendering
│   │   │   ├── email.py                 <- EmailService: follow-up email draft
│   │   │   └── dashboard.py             <- DashboardService: stats + insights
│   │   ├── ai/                          <- LangGraph pipeline + Gemini SDK isolation
│   │   │   ├── llm.py                   <- ONLY file importing google-genai SDK
│   │   │   ├── outputs.py               <- Pydantic schemas = Gemini response_schema contracts
│   │   │   ├── health.py                <- compute_health(): deterministic rubric, NOT an LLM call
│   │   │   ├── graph.py                 <- build_pipeline(): the LangGraph StateGraph itself
│   │   │   └── prompts/__init__.py      <- one prompt-builder function per agent
│   │   ├── transcription/               <- provider strategy pattern
│   │   │   ├── base.py                  <- TranscriptionProvider Protocol, SegmentIn, TranscriptResult, get_provider()
│   │   │   ├── deepgram.py              <- DeepgramProvider (primary, diarization)
│   │   │   └── whisper.py               <- WhisperProvider (fallback, no diarization)
│   │   ├── workers/
│   │   │   └── dispatcher.py            <- PipelineDispatcher: in-process asyncio job runner
│   │   └── api/
│   │       ├── deps.py                  <- DI wiring: SessionDep, UserDep, *ServiceDep
│   │       └── v1/
│   │           ├── router.py            <- api_router aggregates all v1 routers
│   │           ├── meetings.py          <- /meetings CRUD + /process
│   │           ├── transcripts.py       <- /meetings/{id}/transcript, speaker rename
│   │           ├── reports.py           <- /meetings/{id}/report, /analytics
│   │           ├── action_items.py      <- /meetings/{id}/action-items, /action-items/{id}
│   │           ├── chat.py              <- /meetings/{id}/chat
│   │           ├── exports.py           <- /meetings/{id}/export, /follow-up-email
│   │           └── dashboard.py         <- /dashboard/stats, /dashboard/insights
│   └── tests/                           <- unit/service tests, no DB/network (fakes)
│       ├── test_health_score.py
│       ├── test_processing_utils.py
│       ├── test_meeting_service.py
│       └── test_export_markdown.py
│
├── frontend/                            <- React SPA, deployed to Vercel
│   ├── package.json / vite.config.ts / tsconfig.json / tailwind.config.ts / postcss.config.js
│   ├── vercel.json                      <- SPA rewrite (all routes -> index.html)
│   ├── 
│   ├── index.html
│   └── src/
│       ├── main.tsx                     <- ReactDOM.createRoot -> AppProviders
│       ├── index.css                    <- Tailwind directives, dark scrollbars
│       ├── vite-env.d.ts                <- import.meta.env typing
│       ├── app/
│       │   ├── providers.tsx            <- QueryClientProvider + AuthProvider + RouterProvider
│       │   ├── AuthProvider.tsx         <- Supabase session context (useAuth hook)
│       │   ├── router.tsx               <- createBrowserRouter, all routes
│       │   └── AppLayout.tsx            <- sidebar (desktop) / top bar (mobile), auth guard
│       ├── types/
│       │   └── api.ts                   <- hand-kept mirror of backend Pydantic schemas
│       ├── lib/
│       │   ├── supabase.ts              <- createClient() singleton
│       │   ├── api.ts                   <- fetch wrapper (JWT header, error envelope, upload/download helpers)
│       │   ├── cn.ts                    <- clsx + tailwind-merge helper
│       │   ├── format.ts                <- formatMs/formatDuration/formatBytes/formatDate/timeAgo
│       │   └── format.test.ts           <- vitest unit tests for format.ts
│       ├── components/
│       │   ├── ui/                      <- shadcn-style primitives: button, card, input, textarea,
│       │   │                               badge, dialog, tabs, skeleton, progress, select
│       │   └── shared/                  <- cross-feature composites: HealthRing, StatusBadge,
│       │                                    EmptyState, StatCard
│       └── features/
│           ├── auth/AuthPage.tsx        <- login/signup split-screen
│           ├── dashboard/DashboardPage.tsx
│           ├── meetings/
│           │   ├── MeetingsPage.tsx     <- search/filter/paginate list
│           │   ├── MeetingRow.tsx
│           │   ├── UploadDialog.tsx     <- drag-drop, direct-to-storage upload, progress
│           │   ├── MeetingDetailPage.tsx<- header + 5 tabs + processing/failed states
│           │   ├── ProcessingView.tsx   <- polled pipeline stage tracker
│           │   ├── OverviewTab.tsx      <- report: summary/decisions/risks/topics/health
│           │   ├── TranscriptTab.tsx    <- topic timeline strip + diarized segments + speaker rename
│           │   ├── ActionItemsTab.tsx   <- editable table
│           │   ├── AnalyticsTab.tsx     <- talk-time pie, contributions bar, topic-by-speaker table
│           │   └── ChatTab.tsx          <- RAG chat UI with timestamp source chips
│           └── export/
│               ├── ExportMenu.tsx       <- pdf/md/txt download dropdown
│               └── FollowUpEmailDialog.tsx
│
└── tests/                               <- cross-service ONLY (unit tests live with their package)
    ├── README.md
    └── e2e/
        ├── playwright.config.ts
        └── upload-flow.spec.ts          <- full upload->report->chat flow, self-skips w/o creds
```

---

## 4. Data model (database/schema.sql)

Postgres on Supabase. Extensions: `vector` (pgvector), `pg_trgm` (fuzzy title search).

**Enums**: `meeting_status` (`uploading|uploaded|transcribing|analyzing|completed|failed`),
`action_item_priority` (`low|medium|high|urgent`), `action_item_status`
(`open|in_progress|done|blocked`), `chat_role` (`user|assistant`).

**Tables**:
- `profiles` — 1:1 with `auth.users`, auto-provisioned by an `on_auth_user_created` trigger.
- `meetings` — the aggregate root. `user_id`, `title`, `status`, `audio_path` (storage object
  key), `audio_mime`, `audio_size_bytes`, `duration_seconds`, `language`, `error_message`,
  timestamps. Indexed on `(user_id, created_at desc)` and trigram on `title`.
- `transcripts` — 1:1 with meeting. `raw_text`, `cleaned_text`, `provider`, `word_count`,
  generated `tsv` column (full-text search, not currently exposed via API).
- `transcript_segments` — many per meeting. `speaker_label` (`S1`, `S2`, ...), `start_ms`,
  `end_ms`, `text`. This is the timeline/diarization data.
- `speakers` — `meeting_id`, `label` (matches segment label), `display_name` (renameable,
  default `"Speaker 1"`, `"Speaker 2"`, ...). Unique on `(meeting_id, label)`.
- `reports` — 1:1 with meeting. All AI-generated content as `jsonb` columns: `topics`,
  `decisions`, `risks`, `open_questions`, `deadlines`, `next_meeting_agenda`. Plus
  `executive_summary` (text), `health_score` (smallint 0-100, checked), `health_breakdown`
  (jsonb), `agent_warnings` (jsonb — which agents degraded), `model` (which Gemini model ran).
- `action_items` — its own table (not jsonb) because it has an independent mutable lifecycle:
  `task`, `owner`, `due_date`, `priority`, `status`, `sort_order`.
- `transcript_chunks` — RAG store. `chunk_index`, `content`, `start_ms`, `end_ms`,
  `embedding vector(768)`. HNSW index with `vector_cosine_ops`.
- `chat_messages` — `role`, `content`, `sources` (jsonb array of `{chunk_id, start_ms, end_ms}`).
- `processing_events` — append-only log: `stage`, `status` (`started|succeeded|failed`),
  `detail`, `created_at`. Powers both the live progress UI and post-hoc debugging.

**Row Level Security**: enabled on every table. `meetings` policy checks `user_id = auth.uid()`
directly; every child table's policy joins back to `meetings` and checks the same. Child
tables are **select-only** for the Supabase client — all writes go through the FastAPI backend
(which connects with the service-role key and bypasses RLS as the trusted tier; RLS is
defense-in-depth for the anon/authenticated client path).

**Storage**: private bucket `meeting-audio`. Object keys are `{user_id}/{meeting_id}/{filename}`.
Storage policies check `(storage.foldername(name))[1] = auth.uid()::text` for both insert and
select.

---

## 5. Backend architecture (layering and why)

Strict dependency direction: **api → services → repositories → models**. Never the reverse,
never skipped.

- **`api/v1/*.py`** (routers): parse/validate request via Pydantic, call exactly one service
  method, shape the response. Zero business logic. Auth via `UserDep` (verifies JWT → `AuthUser`),
  DB session via `SessionDep`, services via `*ServiceDep` — all wired in `api/deps.py`.
- **`services/*.py`**: own use-cases and orchestration. Depend on repository *instances*
  (constructor-injected), not on FastAPI at all — this is what makes them unit-testable with
  fakes (see `tests/test_meeting_service.py`, which injects a `FakeMeetingRepo`/`FakeStorage`
  with zero DB or network).
- **`repositories/*.py`**: the only place SQLAlchemy queries are written. One class per
  aggregate (`MeetingRepository`, `ActionItemRepository`, etc.), constructed with an
  `AsyncSession`.
- **`models/*.py`**: SQLAlchemy ORM classes. Explicitly **not** the schema owner — comment in
  `models/base.py` says never call `metadata.create_all()`; `database/schema.sql` is canonical.

**Exceptions**: `core/exceptions.py` defines `AppError` and subclasses (`BadRequestError` 400,
`UnauthorizedError` 401, `NotFoundError` 404, `ConflictError` 409, `PayloadTooLargeError` 413,
`UnprocessableAudioError` 422). One exception handler renders every error as
`{"error": {"code", "message", "details"}}`. Unhandled exceptions become a 500 with the same
envelope (never a raw stack trace to the client).

**Config**: `core/config.py` — a `pydantic-settings` `Settings` class, `get_settings()` is
`lru_cache`d. The app fails to boot if required env vars are missing.

**Logging**: `core/logging.py` configures `structlog` — JSON renderer in production, console
renderer in dev. `configure_logging()` is called once in `main.create_app()`.

**Security**: `core/security.py` — `get_current_user()` FastAPI dependency decodes the
Supabase JWT with `PyJWT`, validates signature/audience (`"authenticated"`), returns
`AuthUser(id, email)`. No password ever touches this backend.

---

## 6. The AI pipeline — exact mechanics

Entry point: `services/processing.py :: ProcessingService.run(meeting_id)`, invoked by
`workers/dispatcher.py :: PipelineDispatcher.start(meeting_id)` (fired from the
`POST /meetings/{id}/process` route). Runs as an `asyncio.Task` in the same process as the
API — no external queue (documented tradeoff, see §9).

**Phases inside `ProcessingService._run`** (each phase commits its own DB session so progress
survives a restart mid-pipeline):

1. Load meeting, set `status = "transcribing"`.
2. `StorageClient.create_signed_download_url()` → call `TranscriptionProvider.transcribe()`
   (Deepgram or Whisper per `TRANSCRIPTION_PROVIDER` env var). Returns `TranscriptResult`
   (raw_text, provider, language, duration_seconds, `list[SegmentIn]`).
3. Wipe any previous derived data (idempotent reprocessing on retry), persist
   `Transcript` + `TranscriptSegment` rows + `Speaker` rows (default display names
   `"Speaker 1"`, `"Speaker 2"`, ...). Set `status = "analyzing"`.
4. Build a flattened, speaker-attributed, `[MM:SS]`-timestamped transcript string
   (`build_transcript_text`, capped at `settings.max_prompt_chars`) and per-speaker talk-time
   shares (`compute_talk_shares`). Run `ai/graph.py :: build_pipeline(recorder)` via
   `graph.ainvoke(initial_state)`.
5. Persist the `Report` row and `ActionItem` rows from the graph's final state.
6. Chunk the transcript (`build_chunks`, ~1200 chars/chunk, speaker+timestamp preserved),
   embed via `ai/llm.py :: embed_texts()`, persist `TranscriptChunk` rows. **Non-fatal**: if
   this fails, the report still stands — chat just degrades.
7. Set `status = "completed"`.

Any uncaught exception at the top level sets `status = "failed"` with `error_message`, and the
retry route (`POST /process` again) re-enters at phase 1 (existing derived data is wiped first).

### The LangGraph graph (`ai/graph.py`)

```
START → cleaning → {topics, decisions, action_items, risks, deadlines} (parallel fan-out)
                                      ↓ (join — waits for all 5)
                                   health
                                      ↓
                                  summary → END
```

- **State** (`PipelineState`, a `TypedDict`): `meeting_context`, `transcript_text`,
  `talk_shares`, `cleaned_transcript`, `topics`, `decisions`, `open_questions`,
  `action_items`, `risks`, `deadlines`, `health_score`, `health_breakdown`,
  `executive_summary`, `next_meeting_agenda`, `agent_errors` (merged via `operator.or_` —
  each parallel branch can write its own key without clobbering siblings).
- **`_wrap(name, fn, recorder, fallback)`**: every node is wrapped uniformly — emits a
  `processing_events` row on start/success/failure, and on exception captures the error into
  `agent_errors[name]` instead of raising, so **only the cleaning node has a hard fallback**
  (falls back to the raw uncleaned transcript); the five extractors and the summary agent
  degrade to empty/placeholder output and the meeting still completes.
- Each extraction node (`_topics`, `_decisions`, `_action_items`, `_risks`, `_deadlines`)
  calls `llm.generate_structured(prompt, PydanticSchema)` — Gemini structured JSON output
  validated against a Pydantic schema from `ai/outputs.py`, with up to 2 retries that feed the
  validation error back into the prompt.
- `_health` is **pure Python, not an LLM call** — calls `ai/health.py :: compute_health()`.
- `_summary` runs last so it can reference the already-extracted structured data for
  consistency (fed into the prompt as a JSON blob), using `gemini_summary_model`
  (separately configurable from the extraction model).

### `ai/llm.py` — the only Gemini SDK import

- `generate_structured(prompt, schema, model, temperature, retries)` — JSON mode via
  `response_mime_type="application/json"` + `response_schema=schema`; retries by re-prompting
  with the validation error appended.
- `generate_text(prompt, model, temperature)` — plain text (used for chat answers and, oddly,
  not for email — email uses `generate_structured` with `EmailDraft` schema).
- `embed_texts(texts)` — batches of ≤100, returns `list[list[float]]` (768-dim).

### `ai/health.py` — the deterministic rubric

Five weighted dimensions (`WEIGHTS`): `ownership` 0.25, `deadlines` 0.20, `clarity` 0.25,
`resolution` 0.15, `participation` 0.15. Each dimension is a pure function of already-extracted
data (e.g. ownership = % of action items with an owner; resolution = 100 minus a
severity/blocker-weighted penalty from `risks`; participation penalizes a single speaker
dominating talk time). Returns `(overall_score: int, breakdown: dict[dim -> {score, rationale}])`.
Fully unit-tested in `backend/tests/test_health_score.py` with exact-value assertions —
this is intentional: an LLM-scored health metric would drift and not be comparable across
meetings, so it was made deterministic and testable instead.

### `ai/prompts/__init__.py`

One function per agent (`clean_prompt`, `topics_prompt`, `decisions_prompt`, `actions_prompt`,
`risks_prompt`, `deadlines_prompt`, `summary_prompt`, `email_prompt`, `chat_prompt`). Each is a
plain Python f-string builder — no template engine — versioned as ordinary code, reviewed in
diffs like any other logic.

---

## 7. Transcription provider abstraction

`transcription/base.py` defines:
```python
class TranscriptionProvider(Protocol):
    async def transcribe(self, audio_url: str) -> TranscriptResult: ...
```
`get_provider(settings)` returns `DeepgramProvider` or `WhisperProvider` based on
`settings.transcription_provider`. Adding a new provider (e.g. AssemblyAI) means writing one
new class and adding one `match` arm — nothing else in the codebase changes.

- **`DeepgramProvider`** (`deepgram.py`): calls `nova-3` with `diarize=true`,
  `smart_format=true`, `utterances=true`. Maps Deepgram's numeric speaker IDs to `"S1"`, `"S2"`,
  etc. This is the default because diarization is native — required for the speaker-analytics
  feature and the transcript timeline UI.
- **`WhisperProvider`** (`whisper.py`): streams the signed URL to a temp file, POSTs multipart
  to OpenAI's transcription endpoint with `verbose_json`. **No diarization** — every segment is
  labeled `"S1"`. Documented limitation, used as a no-diarization-hardware-free fallback.

Both raise `UnprocessableAudioError` (422) if the provider returns no speech/errors.

---

## 8. RAG chat (`services/chat.py`)

1. Guard: meeting must belong to the user and `status == "completed"` (else `ConflictError`).
2. Persist the user's message immediately (`ChatMessage(role="user")`).
3. Embed the question (`llm.embed_texts([message])[0]`).
4. `ChunkRepository.search(meeting_id, embedding, k=settings.rag_top_k)` — pgvector
   `cosine_distance` ORDER BY + LIMIT, scoped to the one meeting.
5. Build a labeled excerpt block (`[chunk <id> | <start>-<end>]\n<content>`) and call
   `llm.generate_text(prompts.chat_prompt(question, excerpts))`. The prompt instructs the model
   to answer **only** from the excerpts and say so explicitly if the transcript doesn't cover it
   — no hallucinated answers.
6. Persist the assistant's message with `sources` = top-3 `{chunk_id, start_ms, end_ms}`.
7. Frontend renders `sources` as clickable timestamp chips (`ChatTab.tsx`) that scroll the
   Transcript tab to that segment (`TranscriptTab.tsx :: jumpTo`).

If no chunks exist (embeddings failed at pipeline time), the service returns a canned "can't
answer" message instead of crashing — chat degrades independently of the report.

---

## 9. API surface (full contract)

Base path `/api/v1`. Auth: `Authorization: Bearer <supabase-jwt>` on everything except
`/healthz`. Every meeting-scoped route resolves ownership via `user_id` — a foreign UUID
returns 404, never 403 (no existence leakage across tenants).

| Method | Path | Service method | Notes |
|---|---|---|---|
| POST | `/meetings` | `MeetingService.create` | validates ext/size, returns signed upload URL |
| GET | `/meetings` | `MeetingService.list` | `?q=&status=&page=&page_size=` |
| GET | `/meetings/{id}` | `MeetingService.detail` | meeting + report + speakers |
| GET | `/meetings/{id}/status` | `MeetingService.status` | polled every 2.5s while in-flight |
| PATCH | `/meetings/{id}` | `MeetingService.rename` | |
| DELETE | `/meetings/{id}` | `MeetingService.delete` | also deletes the storage object |
| POST | `/meetings/{id}/process` | dispatcher.start | 202; 409 if already running/completed |
| GET | `/meetings/{id}/transcript` | `TranscriptRepository` (direct) | segments + speakers |
| PATCH | `/meetings/{id}/speakers/{sid}` | `TranscriptRepository` (direct) | rename display_name |
| GET | `/meetings/{id}/report` | `ReportRepository` (direct) | 404 until pipeline completes |
| GET | `/meetings/{id}/analytics` | `AnalyticsService.compute` | computed on demand, not stored |
| GET | `/meetings/{id}/action-items` | `ActionItemRepository` | |
| POST | `/meetings/{id}/action-items` | `ActionItemRepository` | manual add |
| PATCH | `/action-items/{item_id}` | `ActionItemRepository` | partial update (task/owner/due/priority/status) |
| DELETE | `/action-items/{item_id}` | `ActionItemRepository` | |
| GET | `/meetings/{id}/chat` | `ChatService.history` | |
| POST | `/meetings/{id}/chat` | `ChatService.ask` | RAG answer + sources |
| GET | `/meetings/{id}/export?format=pdf\|md\|txt` | `ExportService.export` | streamed file download |
| POST | `/meetings/{id}/follow-up-email` | `EmailService.draft` | `{tone}` -> `{subject, body}` |
| GET | `/dashboard/stats` | `DashboardService.stats` | totals, hours, open/overdue items, health trend |
| GET | `/dashboard/insights` | `DashboardService.insights` | deterministic aggregation, no extra LLM calls |
| GET | `/healthz` | — | liveness, no auth |

Error envelope (every non-2xx response):
```json
{ "error": { "code": "not_found", "message": "Meeting not found", "details": null } }
```

---

## 10. Frontend architecture

**Routing** (`app/router.tsx`): `/login`, `/signup` standalone; everything else nested under
`AppLayout` (auth-guarded — redirects to `/login` if no Supabase session): `/dashboard`,
`/meetings`, `/meetings/:meetingId`.

**Auth** (`app/AuthProvider.tsx`): wraps `supabase.auth.getSession()` +
`onAuthStateChange` into a React context (`useAuth()` → `{session, loading}`).

**Data layer** (`lib/api.ts`): a thin `fetch` wrapper (`api<T>(path, init)`) that attaches the
Supabase JWT as a Bearer header on every call and unwraps the backend's error envelope into a
typed `ApiError`. Two special helpers: `uploadToSignedUrl` (XHR, not fetch, because only XHR
exposes upload progress events — used by the upload dialog's progress bar) and `apiDownload`
(fetches a file with auth headers, since `<a href>` can't attach a Bearer token, then triggers
a browser download via a blob URL).

**State**: TanStack Query for all server state. Meeting detail and status both poll via
`refetchInterval` while the meeting is in an in-flight status
(`uploading|uploaded|transcribing|analyzing`), and stop polling once `completed`/`failed`.

**Types** (`types/api.ts`): a hand-maintained TypeScript mirror of every backend Pydantic
schema. **This is a deliberate manual sync point** — if a backend schema changes, this file
must be updated by hand (no codegen wired up yet).

**Component structure**: `components/ui/` = generic primitives (Button, Card, Input, Textarea,
Badge, Dialog, TabBar, Skeleton, Progress, Select) — all Tailwind-styled, dark-mode-first.
`components/shared/` = cross-feature composites (`HealthRing` — SVG ring gauge, `StatusBadge`,
`EmptyState`, `StatCard`). `features/<name>/` = one folder per product feature, containing its
page(s) and any feature-specific components — the organizing unit is the feature, not the
component type (see `docs/02-folder-structure.md` for the full rationale).

**Key feature flows**:
- `UploadDialog.tsx`: register meeting (`POST /meetings`) → upload bytes directly to the
  returned signed URL via XHR with progress → `POST /meetings/{id}/process` → navigate to the
  meeting detail page.
- `MeetingDetailPage.tsx`: polls `/meetings/{id}`; while in-flight renders `ProcessingView`
  (polls `/status`, shows a stage-by-stage checklist); once `completed`, renders a `TabBar`
  (Overview / Transcript / Action items / Analytics / Chat) each backed by its own query.
- `TranscriptTab.tsx`: renders a topic-colored timeline strip (from `report.topics[].start_ms/
  end_ms`) that's clickable to scroll to that transcript segment; inline speaker rename via
  `PATCH /speakers/{id}`.
- `ChatTab.tsx`: message list + input; assistant messages show timestamp "chips" from
  `sources`; empty state offers starter-question buttons.
- `ExportMenu.tsx` / `FollowUpEmailDialog.tsx`: call the export/email endpoints; email draft is
  editable before a "copy to clipboard" action (no SMTP send in v1, by design).

---

## 11. Testing

- **Backend** (`backend/tests/`, pytest, no DB/network — fakes only):
  - `test_health_score.py` — exact-value assertions on the deterministic rubric.
  - `test_processing_utils.py` — `format_ms`, `build_transcript_text` (+ truncation),
    `compute_talk_shares`, `build_chunks`.
  - `test_meeting_service.py` — `MeetingService.create` against a `FakeMeetingRepo` +
    `FakeStorage`: rejects bad extensions/oversized files, sanitizes the storage path.
  - `test_export_markdown.py` — every report section appears in rendered Markdown; TXT export
    strips markdown tokens.
  - All 15 tests pass; `ruff check` is clean (two FastAPI/typing-idiom rules explicitly
    ignored in `pyproject.toml` with inline justification, not silenced blindly).
- **Frontend** (`frontend/src/**/*.test.ts`, vitest): `lib/format.test.ts` — 7 tests on
  `formatMs`/`formatDuration`/`formatBytes`. `tsc --noEmit --strict` passes clean.
- **E2E** (`tests/e2e/`, Playwright): one spec, `upload-flow.spec.ts`, driving the real
  upload → poll → report → chat flow against a live stack. Self-skips (does not fail CI) when
  `E2E_EMAIL`/`E2E_PASSWORD`/`E2E_AUDIO_FILE` env vars aren't set.

---

## 12. Deployment

- **Backend → Render**: `render.yaml` blueprint, `runtime: docker`, `rootDir: backend`,
  `healthCheckPath: /healthz`. Docker is required specifically because WeasyPrint (PDF export)
  needs native Pango/Cairo libraries installed via `apt-get` in `backend/Dockerfile`. Secrets
  (`DATABASE_URL`, `SUPABASE_*`, `GEMINI_API_KEY`, `DEEPGRAM_API_KEY`, `FRONTEND_ORIGIN`) are
  `sync: false` — set manually in the Render dashboard, never committed.
- **Frontend → Vercel**: root directory `frontend/`, `vercel.json` rewrites every path to
  `/index.html` (SPA routing). Env vars: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`,
  `VITE_API_URL` (the Render backend URL).
- **Database → Supabase**: `database/schema.sql` pasted into the SQL editor once, or applied
  via `supabase db push` per `database/migrations/README.md`.

---

## 13. Known, documented tradeoffs (not oversights)

| Decision now | Reasoning | Upgrade path already designed in |
|---|---|---|
| In-process `asyncio.Task` pipeline runner (`workers/dispatcher.py`) | Zero extra infra for a single-tenant deployment | Swap `PipelineDispatcher.start()` to enqueue into Celery/Arq — nothing upstream (routes, services) changes |
| Status polling every 2.5s, not websockets | Simple, restart-proof, cheap indexed SELECT | Supabase Realtime subscription on `processing_events` |
| Analytics computed on demand, not cached | No second source of truth to keep in sync with `transcript_segments` | Add a cache if profiling ever shows it's needed |
| Single LLM vendor (Gemini) | One vendor to secure/monitor/bill | `ai/llm.py` is the only file touching the SDK — swapping is localized |
| Frontend types hand-mirrored from backend schemas (`types/api.ts`) | No codegen pipeline set up yet | Generate from FastAPI's OpenAPI JSON |
| LangGraph fan-out over a linear chain (deviation from a literal reading of "Transcript → Cleaning → Topic → Decision → Action → Risk → Deadline → Health → Summary") | The five extractors have no data dependency on each other; parallelizing roughly halves wall-clock latency | N/A — this is the final design, not a placeholder |
| Follow-up email is drafted + copy-to-clipboard, no SMTP send | Avoids scope creep / sending-on-behalf-of risk in v1 | Add a mail provider integration later |

---

## 14. Glossary of names you'll see repeated in code

- **`AuthUser`** — `(id: UUID, email: str | None)`, the decoded-JWT identity, threaded through
  every service call as the ownership check parameter.
- **`PipelineState`** — the LangGraph `TypedDict` carrying transcript text, per-agent outputs,
  and `agent_errors` through the graph.
- **`SegmentIn`** — a transcription provider's raw diarized utterance (`speaker_label`,
  `start_ms`, `end_ms`, `text`), before it becomes a DB `TranscriptSegment` row.
- **`ExportFile`** — `(filename, media_type, content: bytes)`, the uniform return type of
  `ExportService.export`, streamed back as a `Response` with `Content-Disposition`.
- **`display_name` vs `label`** on speakers — `label` is the immutable provider ID (`"S1"`);
  `display_name` is the user-renameable name shown in the UI (defaults to `"Speaker 1"`).
