# MeetIQ — Wireframes & Design Language

> Phase 1 · Design doc 4 of 4 · Status: awaiting review

## Design language

Dark-first SaaS dashboard (light mode supported via CSS variables / Tailwind `dark:` inversion).

| Token | Value | Used for |
|---|---|---|
| Background | zinc-950 | app canvas |
| Surface | zinc-900, border zinc-800, rounded-xl | cards, tables, panels |
| Primary accent | indigo-500 | CTAs, active nav, links, focus rings |
| Semantic | emerald (done/healthy) · amber (medium/warning) · rose (urgent/risk/failed) | statuses, priorities, health |
| Type | Inter; 13–14px body, 20/28px section titles, tabular-nums for stats | everything |
| Spacing | 4px grid; cards padded 20–24px | rhythm |
| Motion | 150–200ms ease-out on hover/expand; progress transitions; **no** decorative animation | restraint |
| Charts | Recharts, single-hue depth + semantic colors only | analytics |

Every data view designs its **empty, loading (skeleton), and error states** up front — that, more than anything, is what separates product from prototype.

---

## 1. Auth — `/login`, `/signup`

Split screen: brand left, form right. Collapses to form-only on mobile.

```
┌──────────────────────────────┬──────────────────────────────┐
│                              │                              │
│   ◆ MeetIQ                   │        Welcome back          │
│                              │                              │
│   Transform meetings into    │   Email                      │
│   structured business        │   [_______________________]  │
│   intelligence.              │   Password                   │
│                              │   [_______________________]  │
│   ▸ AI reports & health      │                              │
│   ▸ Action-item tracking     │   [████  Sign in  ████]      │
│   ▸ Chat with any meeting    │                              │
│                              │   No account? Sign up →      │
└──────────────────────────────┴──────────────────────────────┘
```

## 2. Dashboard — `/dashboard`

```
┌────────┬────────────────────────────────────────────────────────────┐
│        │  Good morning, Alex                    [＋ Upload meeting]  │
│ ◆      │                                                            │
│ MeetIQ │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│        │  │ Meetings │ │ Hours    │ │ Open     │ │ Avg      │       │
│ ▸ Dash │  │   24     │ │ processed│ │ actions  │ │ health   │       │
│ ▸ Meet │  │ +3 this  │ │  18.5    │ │   12     │ │  76 ◔    │       │
│ ▸ Acts │  │   week   │ │          │ │ 3 overdue│ │          │       │
│        │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│        │                                                            │
│        │  ┌ AI Insights ─────────────────────────────────────────┐  │
│        │  │ ⚠ "Deployment ownership" unresolved in 3 meetings    │  │
│        │  │ ⚠ 3 action items overdue, all owned by Rahul         │  │
│        │  └──────────────────────────────────────────────────────┘  │
│        │                                                            │
│        │  Recent meetings           [Search…____________] [Filter]  │
│        │  ┌──────────────────────────────────────────────────────┐  │
│        │  │ Q3 Planning Sync    ● completed   74 ◔   2h ago    → │  │
│        │  │ Design review       ◌ analyzing   ▓▓▓░░  12m ago     │  │
│        │  │ Vendor call         ● completed   81 ◔   Jul 10   → │  │
│        │  └──────────────────────────────────────────────────────┘  │
│ ⚙ ⏻   │                                                            │
└────────┴────────────────────────────────────────────────────────────┘
```

In-flight meetings show a live stage progress bar (from the polled status endpoint) directly in the list row.

## 3. Upload — modal over dashboard

```
┌─ Upload meeting ────────────────────────────────┐
│                                                 │
│   ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐      │
│         ⬆  Drag & drop audio/video             │
│   │      or click to browse               │     │
│         mp3 · wav · mp4 · m4a  (≤500MB)         │
│   └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘      │
│                                                 │
│   Title  [ Q3 Planning Sync____________ ]       │
│                                                 │
│   q3-sync.mp3   46 MB                           │
│   ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░  62%  ·  cancel         │
│                                                 │
│                        [Cancel] [Upload & analyze] │
└─────────────────────────────────────────────────┘
```

After upload confirms, the modal hands off to the meeting page, which shows the pipeline stage tracker: `Transcribe ✓ → Clean ✓ → Analyze ◌ → Report …`

## 4. Meeting detail — `/meetings/:id`

Header + five tabs. Header is persistent: title, date, duration, status, health ring, and actions (Export ▾, Follow-up email, Delete).

```
┌──────────────────────────────────────────────────────────────────┐
│ ← Q3 Planning Sync        Jul 12 · 48 min · ● completed          │
│   Health 74 ◔      [✉ Follow-up email] [⬇ Export ▾ pdf/md/txt]  │
├──────────────────────────────────────────────────────────────────┤
│ [ Overview ] [ Transcript ] [ Action items ] [ Analytics ] [ Chat ] │
└──────────────────────────────────────────────────────────────────┘
```

**Overview tab** — the report:

```
┌ Executive summary ───────────────────────────────────────────────┐
│ …                                                                │
└──────────────────────────────────────────────────────────────────┘
┌ Decisions (3) ──────────────┐  ┌ Risks & blockers (2) ───────────┐
│ ✓ Adopt Supabase — Priya    │  │ ▲ high  Deployment owner unclear │
└─────────────────────────────┘  └─────────────────────────────────┘
┌ Key topics ── timeline strip: [intro|budget ▓▓▓|vendor|auth ▓] ──┐
└──────────────────────────────────────────────────────────────────┘
┌ Open questions ─────────────┐  ┌ Health breakdown ───────────────┐
│ ? SOC2 before launch?       │  │ Ownership   ▓▓▓░░ 60            │
└─────────────────────────────┘  │ Deadlines   ▓▓▓▓░ 80            │
┌ Next meeting agenda ────────┐  │ Clarity     ▓▓▓▓░ 85            │
│ 1. Vendor shortlist …       │  └─────────────────────────────────┘
└─────────────────────────────┘
```

**Transcript tab** — timeline strip on top (topic-colored, clickable to seek); diarized segments below; speaker names editable inline (pencil → rename `S1` everywhere).

```
[ 00:00 ─────▓▓budget▓▓────vendor────▓auth▓─────── 48:00 ]
┌──────────────────────────────────────────────────────────┐
│ 02:03  Priya ✎   We need to re-forecast Q3 spend…        │
│ 02:41  Rahul ✎   The vendor quote came in 20% over…      │
└──────────────────────────────────────────────────────────┘
```

**Action items tab** — editable table: Task · Owner · Deadline · Priority (colored chip) · Status (dropdown: open/in progress/done/blocked). Row add/delete. Overdue deadlines render rose.

**Analytics tab** — talk-time donut, contributions bar chart per speaker, topics-per-speaker matrix.

**Chat tab** — thread UI; assistant answers carry source chips (`▶ 30:34`) that jump to the transcript at that timestamp. Suggested starter questions when history is empty.

```
┌──────────────────────────────────────────────┐
│ You: Who owns deployment?                    │
│ MeetIQ: It was raised but never assigned.    │
│         Rahul volunteered to investigate…    │
│         [▶ 30:34] [▶ 31:12]                  │
│                                              │
│ [Ask about this meeting…____________] [Send] │
└──────────────────────────────────────────────┘
```

## 5. Follow-up email — dialog

Tone selector (formal / friendly / brief) → generated subject + body in an editable textarea → **Copy to clipboard**. We generate the email; the user sends it from their own client — no SMTP scope creep in v1.

## Responsive behavior

- Sidebar → bottom tab bar under 768px; stat cards 4→2→1 columns.
- Meeting tabs become horizontally scrollable; tables collapse to cards on mobile.
- Transcript timeline strip stays — it's the signature interaction.
