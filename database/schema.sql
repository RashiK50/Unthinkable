-- ============================================================
-- MeetIQ — canonical database schema (Phase 1)
-- Target: Supabase Postgres 15+
-- Apply with: supabase db push, or paste into the SQL editor.
--
-- Conventions:
--   * uuid PKs via gen_random_uuid() (built into PG13+)
--   * enums for user-facing state machines (invalid states unrepresentable)
--   * RLS enabled on EVERY table. The FastAPI backend connects with a
--     privileged role and bypasses RLS; these policies are defense-in-depth
--     for the Supabase client path (anon/authenticated keys).
--   * timestamps are timestamptz, UTC always.
-- ============================================================

create extension if not exists vector;      -- pgvector: transcript chunk embeddings
create extension if not exists pg_trgm;     -- fuzzy title search

-- ---------- enums ----------

create type meeting_status as enum (
  'uploading', 'uploaded', 'transcribing', 'analyzing', 'completed', 'failed'
);

create type action_item_priority as enum ('low', 'medium', 'high', 'urgent');
create type action_item_status   as enum ('open', 'in_progress', 'done', 'blocked');
create type chat_role            as enum ('user', 'assistant');

-- ---------- helper: updated_at maintenance ----------

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;

-- ---------- profiles (1:1 with auth.users) ----------

create table public.profiles (
  id         uuid primary key references auth.users (id) on delete cascade,
  full_name  text,
  avatar_url text,
  created_at timestamptz not null default now()
);

-- auto-provision a profile row on signup (standard Supabase pattern)
create or replace function public.handle_new_user()
returns trigger
language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, full_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'full_name', ''));
  return new;
end $$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------- meetings ----------

create table public.meetings (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references auth.users (id) on delete cascade,
  title            text not null,
  status           meeting_status not null default 'uploading',
  audio_path       text,            -- object key in the meeting-audio bucket
  audio_mime       text,
  audio_size_bytes bigint,
  duration_seconds integer,
  language         text,
  error_message    text,            -- populated only when status = 'failed'
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

create index idx_meetings_user_recent on public.meetings (user_id, created_at desc);
create index idx_meetings_title_trgm  on public.meetings using gin (title gin_trgm_ops);

create trigger trg_meetings_updated_at
  before update on public.meetings
  for each row execute function public.set_updated_at();

-- ---------- transcripts (1:1 with meeting) ----------

create table public.transcripts (
  id           uuid primary key default gen_random_uuid(),
  meeting_id   uuid not null unique references public.meetings (id) on delete cascade,
  raw_text     text not null,
  cleaned_text text,                -- output of the Cleaning Agent
  provider     text not null,       -- 'deepgram' | 'whisper' | ...
  word_count   integer,
  tsv          tsvector generated always as (to_tsvector('english', coalesce(raw_text, ''))) stored,
  created_at   timestamptz not null default now()
);

create index idx_transcripts_tsv on public.transcripts using gin (tsv);

-- ---------- diarized segments (timeline, analytics, chat citations) ----------

create table public.transcript_segments (
  id            bigint generated always as identity primary key,
  meeting_id    uuid not null references public.meetings (id) on delete cascade,
  speaker_label text not null,      -- provider label: 'S1', 'S2', ...
  start_ms      integer not null,
  end_ms        integer not null,
  text          text not null
);

create index idx_segments_meeting_time on public.transcript_segments (meeting_id, start_ms);

-- ---------- speakers (rename 'S1' -> 'Rahul') ----------

create table public.speakers (
  id           uuid primary key default gen_random_uuid(),
  meeting_id   uuid not null references public.meetings (id) on delete cascade,
  label        text not null,       -- matches transcript_segments.speaker_label
  display_name text not null,
  unique (meeting_id, label)
);

-- ---------- intelligence report (1:1 with meeting) ----------

create table public.reports (
  id                   uuid primary key default gen_random_uuid(),
  meeting_id           uuid not null unique references public.meetings (id) on delete cascade,
  executive_summary    text not null,
  topics               jsonb not null default '[]',  -- [{title, summary, start_ms, end_ms}]
  decisions            jsonb not null default '[]',  -- [{decision, context, made_by}]
  risks                jsonb not null default '[]',  -- [{description, kind: 'risk'|'blocker', severity}]
  open_questions       jsonb not null default '[]',  -- [{question, raised_by}]
  deadlines            jsonb not null default '[]',  -- [{item, date_text, date_normalized}]
  next_meeting_agenda  jsonb not null default '[]',  -- [string]
  health_score         smallint not null check (health_score between 0 and 100),
  health_breakdown     jsonb not null default '{}',  -- {dimension: {score, rationale}}
  agent_warnings       jsonb not null default '{}',  -- {agent: error} — graceful degradation
  model                text not null,                -- e.g. 'gemini-2.5-flash'
  created_at           timestamptz not null default now()
);

-- ---------- action items (own table: independently editable state) ----------

create table public.action_items (
  id         uuid primary key default gen_random_uuid(),
  meeting_id uuid not null references public.meetings (id) on delete cascade,
  task       text not null,
  owner      text,                              -- speaker display name or free text
  due_date   date,
  priority   action_item_priority not null default 'medium',
  status     action_item_status   not null default 'open',
  sort_order integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_action_items_meeting on public.action_items (meeting_id, sort_order);

create trigger trg_action_items_updated_at
  before update on public.action_items
  for each row execute function public.set_updated_at();

-- ---------- RAG chunks for transcript chat ----------
-- ~500-token chunks of the cleaned transcript, speaker + timestamps preserved.
-- Embeddings: Gemini text-embedding-004 → 768 dimensions.

create table public.transcript_chunks (
  id          bigint generated always as identity primary key,
  meeting_id  uuid not null references public.meetings (id) on delete cascade,
  chunk_index integer not null,
  content     text not null,
  start_ms    integer,
  end_ms      integer,
  embedding   vector(768),
  unique (meeting_id, chunk_index)
);

create index idx_chunks_embedding on public.transcript_chunks
  using hnsw (embedding vector_cosine_ops);

-- ---------- chat history ----------

create table public.chat_messages (
  id         uuid primary key default gen_random_uuid(),
  meeting_id uuid not null references public.meetings (id) on delete cascade,
  user_id    uuid not null references auth.users (id) on delete cascade,
  role       chat_role not null,
  content    text not null,
  sources    jsonb not null default '[]',  -- [{chunk_id, start_ms, end_ms}] for citations
  created_at timestamptz not null default now()
);

create index idx_chat_meeting_time on public.chat_messages (meeting_id, created_at);

-- ---------- processing event log (progress UI + debugging) ----------

create table public.processing_events (
  id         bigint generated always as identity primary key,
  meeting_id uuid not null references public.meetings (id) on delete cascade,
  stage      text not null,   -- 'transcription', 'cleaning', 'topics', ...
  status     text not null check (status in ('started', 'succeeded', 'failed')),
  detail     text,
  created_at timestamptz not null default now()
);

create index idx_events_meeting on public.processing_events (meeting_id, created_at);

-- ============================================================
-- Row Level Security
-- Pattern: meetings gate on user_id; child tables gate through
-- their parent meeting. Backend (privileged role) bypasses all of this.
-- ============================================================

alter table public.profiles            enable row level security;
alter table public.meetings            enable row level security;
alter table public.transcripts         enable row level security;
alter table public.transcript_segments enable row level security;
alter table public.speakers            enable row level security;
alter table public.reports             enable row level security;
alter table public.action_items        enable row level security;
alter table public.transcript_chunks   enable row level security;
alter table public.chat_messages       enable row level security;
alter table public.processing_events   enable row level security;

create policy "own profile" on public.profiles
  for all to authenticated
  using (id = auth.uid()) with check (id = auth.uid());

create policy "own meetings" on public.meetings
  for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

-- child-table policy factory (same shape for each child table)
create policy "via own meeting" on public.transcripts
  for select to authenticated
  using (exists (select 1 from public.meetings m
                 where m.id = meeting_id and m.user_id = auth.uid()));

create policy "via own meeting" on public.transcript_segments
  for select to authenticated
  using (exists (select 1 from public.meetings m
                 where m.id = meeting_id and m.user_id = auth.uid()));

create policy "via own meeting" on public.speakers
  for select to authenticated
  using (exists (select 1 from public.meetings m
                 where m.id = meeting_id and m.user_id = auth.uid()));

create policy "via own meeting" on public.reports
  for select to authenticated
  using (exists (select 1 from public.meetings m
                 where m.id = meeting_id and m.user_id = auth.uid()));

create policy "via own meeting" on public.action_items
  for select to authenticated
  using (exists (select 1 from public.meetings m
                 where m.id = meeting_id and m.user_id = auth.uid()));

create policy "via own meeting" on public.transcript_chunks
  for select to authenticated
  using (exists (select 1 from public.meetings m
                 where m.id = meeting_id and m.user_id = auth.uid()));

create policy "via own meeting" on public.chat_messages
  for select to authenticated
  using (exists (select 1 from public.meetings m
                 where m.id = meeting_id and m.user_id = auth.uid()));

create policy "via own meeting" on public.processing_events
  for select to authenticated
  using (exists (select 1 from public.meetings m
                 where m.id = meeting_id and m.user_id = auth.uid()));

-- Note: child tables are select-only for clients on purpose. All writes go
-- through the FastAPI backend, which owns validation and business rules.

-- ============================================================
-- Storage: private bucket, per-user folders, signed URLs only
-- Object keys: {user_id}/{meeting_id}/{filename}
-- ============================================================

insert into storage.buckets (id, name, public)
values ('meeting-audio', 'meeting-audio', false)
on conflict (id) do nothing;

create policy "users upload to own folder" on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'meeting-audio'
    and (storage.foldername(name))[1] = auth.uid()::text
  );

create policy "users read own folder" on storage.objects
  for select to authenticated
  using (
    bucket_id = 'meeting-audio'
    and (storage.foldername(name))[1] = auth.uid()::text
  );
