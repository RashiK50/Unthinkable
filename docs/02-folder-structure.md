# MeetIQ — Monorepo Structure

> Phase 1 · Design doc 2 of 4 · Status: awaiting review

One repository, hard boundaries inside it. A monorepo is right here because frontend and backend share one API contract and one reviewer will read both; separate repos would add coordination cost and buy nothing for a two-deployable product.

```
meeting_summarizer/              # repo root
├── frontend/                    # React SPA → Vercel
│   ├── src/
│   │   ├── app/                 # app shell: router, providers, layouts, guards
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui primitives (generated, don't hand-edit)
│   │   │   └── shared/          # cross-feature composites: PageHeader, EmptyState,
│   │   │                        #   StatCard, ConfirmDialog, HealthScoreRing…
│   │   ├── features/            # ← the unit of organization (see rationale)
│   │   │   ├── auth/            # login/signup forms, session hooks
│   │   │   ├── dashboard/       # stats, recent meetings, insights
│   │   │   ├── meetings/        # upload flow, list/search, detail tabs, timeline
│   │   │   ├── action-items/    # table, status/priority editing
│   │   │   ├── chat/            # transcript Q&A panel
│   │   │   └── export/          # export menu, follow-up email dialog
│   │   ├── hooks/               # generic hooks (useDebounce, usePolling)
│   │   ├── lib/                 # apiClient (fetch + auth header + error mapping),
│   │   │                        #   supabaseClient, formatters
│   │   └── types/               # API contract types, mirrors backend schemas/
│   ├── index.html · vite.config.ts · tailwind.config.ts · tsconfig.json
│   └── package.json
│
├── backend/                     # FastAPI → Render (Docker)
│   ├── app/
│   │   ├── main.py              # app factory: middleware, routers, exception handlers
│   │   ├── api/
│   │   │   └── v1/              # routers only — parse, call service, shape response
│   │   ├── core/                # config (pydantic-settings), security (JWT verify),
│   │   │                        #   logging, exception hierarchy, DI wiring
│   │   ├── db/                  # async engine/session factory
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── repositories/        # ALL SQL lives here, behind interfaces
│   │   ├── services/            # business logic, transactions, use-cases
│   │   ├── ai/
│   │   │   ├── graph.py         # LangGraph wiring (nodes, fan-out, joins)
│   │   │   ├── agents/          # one module per agent, one job each
│   │   │   ├── prompts/         # prompt templates, versioned as code
│   │   │   └── llm.py           # Gemini client factory (only file importing the SDK)
│   │   ├── transcription/       # TranscriptionProvider protocol + deepgram.py, whisper.py
│   │   └── workers/             # PipelineDispatcher + background runner
│   ├── tests/                   # backend unit + integration tests (mirrors app/)
│   ├── Dockerfile
│   └── pyproject.toml
│
├── database/
│   ├── schema.sql               # canonical current schema — Phase 1 deliverable
│   └── migrations/              # ordered SQL migrations (supabase CLI format)
│
├── docs/                        # these design docs, wireframes, later ADRs
├── tests/                       # cross-service e2e (Playwright) — Phase 7
├── .env.example                 # every required variable, documented, no values
└── README.md                    # Phase 8
```

## Rationale — the choices a reviewer will ask about

**Frontend by feature, not by type.** `features/meetings/` contains its components, hooks, and API calls together. When you touch the upload flow, everything you need is in one folder. Type-based layouts (`components/`, `containers/`, `pages/`) scatter one feature across five directories and rot as the app grows. `components/shared/` is only for things *provably* used by 2+ features — the default home for new code is inside a feature.

**Backend layers are dependency-directed.** `api → services → repositories → models`, never backwards, never skipping. Enforced by convention now, by import-linter in Phase 7. The payoff is stated in the architecture doc §2.4: services get tested with fake repositories, fast and DB-free.

**`ai/` is a package, not a corner of `services/`.** The LangGraph pipeline is the product's core IP and its most volatile code (prompts change weekly). Isolating it means: prompts are versioned files, each agent is testable against recorded transcripts without HTTP or DB, and the Gemini SDK is imported in exactly one place — swapping models or providers touches `llm.py` and config, nothing else.

**`database/` is top-level, not inside `backend/`.** The schema is owned by the *product*, not by one consumer of it — RLS policies and storage policies serve the Supabase client path, which the backend doesn't even use. Raw SQL migrations via the supabase CLI beat Alembic here because RLS, triggers on `auth.users`, and storage policies are Postgres/Supabase-native and awkward to express in ORM-migration DSLs.

**Tests: one adaptation from the brief.** The brief asks for a top-level `tests/`. Unit and integration tests will live *with their package* (`backend/tests/`, colocated `*.test.tsx` in frontend) because tests that live far from the code they test don't get run or updated. The top-level `tests/` is reserved for what genuinely spans both deployables: Playwright e2e flows (upload → process → report → export). This honors the brief's intent — visible, first-class testing — while following ecosystem convention. Flagged for your approval.
