# MeetIQ — API Design

> Phase 1 · Design doc 3 of 4 · Status: awaiting review

## Conventions

| Concern | Convention |
|---|---|
| Base path | `/api/v1` — versioned from day one; v2 is additive, never a breaking rename |
| Auth | `Authorization: Bearer <supabase-jwt>` on every endpoint except `/healthz`. Signup/login happen **client-side against Supabase Auth** — our API never sees credentials, it only verifies tokens (`get_current_user` dependency: signature, `exp`, `aud`). |
| IDs | UUIDs, always server-generated |
| Pagination | `?page=1&page_size=20` → `{ "items": [...], "total", "page", "page_size" }` |
| Errors | One envelope, every failure: `{ "error": { "code": "not_found", "message": "Meeting not found", "details": null } }` |
| Ownership | Every handler resolves resources through the current user; a foreign UUID returns `404` (not `403` — we don't confirm existence of other tenants' data) |

**Error codes:** `validation_error` 400 · `unauthorized` 401 · `not_found` 404 · `conflict` 409 (e.g. processing already running) · `payload_too_large` 413 · `unprocessable_audio` 422 · `rate_limited` 429 · `internal_error` 500.

---

## Endpoints

### Meetings & upload

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/meetings` | Register meeting, get signed upload URL |
| POST | `/api/v1/meetings/{id}/process` | Confirm upload, start pipeline → `202` |
| GET | `/api/v1/meetings` | List + search (`?q=&status=&page=`) |
| GET | `/api/v1/meetings/{id}` | Full detail: meeting + report + speakers |
| GET | `/api/v1/meetings/{id}/status` | Coarse status + stage events (polled) |
| PATCH | `/api/v1/meetings/{id}` | Rename |
| DELETE | `/api/v1/meetings/{id}` | Delete meeting + storage object |

### Transcript & speakers

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/meetings/{id}/transcript` | Segments with speakers + timestamps |
| PATCH | `/api/v1/meetings/{id}/speakers/{speaker_id}` | Rename `S1` → `"Rahul"` |

### Intelligence

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/meetings/{id}/report` | Full intelligence report |
| GET | `/api/v1/meetings/{id}/analytics` | Talk time, contribution counts, topics per speaker (computed from segments) |

### Action items

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/meetings/{id}/action-items` | List |
| POST | `/api/v1/meetings/{id}/action-items` | Add manually |
| PATCH | `/api/v1/action-items/{item_id}` | Edit task/owner/deadline/priority/status |
| DELETE | `/api/v1/action-items/{item_id}` | Remove |

### Chat, email, export

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/meetings/{id}/chat` | Chat history |
| POST | `/api/v1/meetings/{id}/chat` | Ask a question → answer + cited sources |
| POST | `/api/v1/meetings/{id}/follow-up-email` | Generate follow-up email (`{tone}`) |
| GET | `/api/v1/meetings/{id}/export?format=pdf\|md\|txt` | File download |

### Dashboard & ops

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/dashboard/stats` | Totals, hours processed, open action items, avg health, 30-day trend |
| GET | `/api/v1/dashboard/insights` | Cross-meeting insights aggregated from stored reports |
| GET | `/healthz` | Liveness (no auth) |

---

## The upload → report flow (the flow that matters most)

```
1. POST /api/v1/meetings                     → 201 + signed upload URL
2. Client PUTs audio directly to Supabase Storage (progress bar = XHR events)
3. POST /api/v1/meetings/{id}/process        → 202, pipeline starts
4. GET  /api/v1/meetings/{id}/status         → poll every ~2.5s until completed|failed
5. GET  /api/v1/meetings/{id}                → render the report
```

**1 — Register:**

```jsonc
// POST /api/v1/meetings
{ "title": "Q3 Planning Sync", "filename": "q3-sync.mp3",
  "content_type": "audio/mpeg", "size_bytes": 48211003 }

// 201
{ "meeting": { "id": "9b2e…", "title": "Q3 Planning Sync", "status": "uploading",
               "created_at": "2026-07-12T10:04:11Z" },
  "upload": { "signed_url": "https://…", "path": "usr-uuid/9b2e…/q3-sync.mp3",
              "expires_in": 3600 } }
```

Server validates extension/MIME (`mp3`, `wav`, `mp4`, `m4a`) and size cap (500 MB) *before* issuing the URL — reject early, not after a 20-minute upload.

**4 — Status (polled):**

```jsonc
// GET /api/v1/meetings/9b2e…/status → 200
{ "status": "analyzing",
  "stages": [
    { "stage": "transcription", "status": "succeeded", "finished_at": "…" },
    { "stage": "cleaning",      "status": "succeeded", "finished_at": "…" },
    { "stage": "topics",        "status": "started" }
  ] }
```

**Report (shape mirrors the `reports` table):**

```jsonc
// GET /api/v1/meetings/9b2e…/report → 200
{ "executive_summary": "…",
  "topics":    [ { "title": "Budget re-forecast", "summary": "…", "start_ms": 122000, "end_ms": 561000 } ],
  "decisions": [ { "decision": "Adopt Supabase for auth", "context": "…", "made_by": "Priya" } ],
  "risks":     [ { "description": "Deployment owner unclear", "kind": "blocker", "severity": "high" } ],
  "open_questions": [ { "question": "Do we need SOC2 before launch?", "raised_by": "Rahul" } ],
  "deadlines": [ { "item": "Vendor contract signature", "date_text": "end of next week", "date_normalized": "2026-07-24" } ],
  "next_meeting_agenda": [ "Review vendor shortlist", "Confirm deployment owner" ],
  "health": { "score": 74, "breakdown": {
      "ownership":  { "score": 60, "rationale": "2 of 5 action items lack an owner" },
      "deadlines":  { "score": 80, "rationale": "…" } } },
  "agent_warnings": {} }
```

**Chat:**

```jsonc
// POST /api/v1/meetings/9b2e…/chat
{ "message": "Who owns deployment?" }

// 200
{ "answer": "Deployment ownership was raised but not resolved. Rahul volunteered…",
  "sources": [ { "chunk_id": 41, "start_ms": 1834000, "end_ms": 1901000 } ] }
```

`sources` lets the UI deep-link into the transcript timeline — answers are verifiable, not oracle pronouncements.

---

## Design notes

- **Why `POST /process` is separate from `POST /meetings`:** the client owns the upload; the server can't know when the bytes have landed. An explicit confirmation step also gives us a natural retry point (`failed → POST /process` again).
- **Why `202` + polling, not a long-lived request:** pipeline runtime (minutes) exceeds every sane HTTP timeout; see architecture §2.3.
- **Why action items are `PATCH`-able rows, not part of the report blob:** they have a lifecycle (status, owner edits) independent of the immutable AI-generated report — mutable state gets a table, generated artifacts get jsonb.
- **Why `analytics` is computed, not stored:** it's a pure function of `transcript_segments`; storing it would create a second source of truth to keep in sync. Cache later if profiling says so.
