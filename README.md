# Attune

> Goal-aware email triage. Knows what matters *right now*, not just who it's from.

Attune reads your Gmail and Google Calendar, then uses an LLM to label every email against your current goals and deadlines — not static rules. **URGENT** triggers a desktop notification. Everything else goes into a daily digest.

---

## The core idea

Existing tools (Superhuman, Gmail filters) treat urgency as a property of the sender or subject. It isn't.

The same email from your supervisor can be:

| Context | Label |
|---|---|
| Defense in 74 days, light week | `SOON` — read today |
| Defense in 8 days, calendar slammed | `URGENT` — stop what you're doing |

Attune reasons about this. Before triaging a single email, it builds a context bundle from your calendar: today's load, the week ahead, and named milestones with days-to-deadline. Then it judges each email against your natural-language goals.

---

## Architecture

```
Gmail ──────────────────────────────────────┐
                                            ▼
Google Calendar ──────────────────► Context Bundle ──► TriageAgent (LLM)
                                            ▲                │
goals.yaml ─────────────────────────────────┘                │
                                                    ┌────────┴────────┐
                                                    │                 │
                                                URGENT            SOON / LATER / IGNORE
                                                    │                 │
                                            Desktop notification  Daily digest
```

### Goals — natural language, not rules

```yaml
# config/goals.yaml
goals:
  - I am finishing my PhD thesis. My defense is in July 2026.
    Feedback from my supervisor and messages from my thesis committee are critical.
    Anything related to the viva, defense scheduling, or thesis corrections is high priority.

  - I am actively applying for postdoc positions and research grants.
    Funding decisions, grant deadlines, and interview invitations are urgent.

  - I am building a side project with a collaborator.
    Messages about the project are important, especially around technical decisions.

  - Physical activity and social plans with close friends matter for my wellbeing.
    Let those messages through, but they are rarely urgent.
```

No keyword maintenance. No missed edge cases. Update the file when your life changes.

### Calendar context — three layers

| Layer | What it captures |
|---|---|
| **Today's load** | Hours blocked, named events |
| **Week ahead** | Busyness per day (light / moderate / heavy) |
| **Upcoming milestones** | Named deadlines + days away |

### Labels

| Label | Meaning | Action |
|---|---|---|
| `URGENT` | Action required, delay has real cost given imminent milestones. Max 0–2/day. | Desktop notification |
| `SOON` | Read today, respond before EOD | Digest (top) |
| `LATER` | This week, no immediate pressure | Digest |
| `IGNORE` | Not worth your time | Digest (collapsed) |

---

## Two modes

### `attune digest` — batch triage

Run once, get a prioritised snapshot of your inbox.

```
──────────────────────────────────────────────────────────
  TODAY'S DIGEST (Sun May 3)
  Today: moderate  ·  Week ahead: L H M M L L L
  Milestones: Veni grant in 2d · Chapter 3 in 3d · ICML in 5d · Defense in 74d
──────────────────────────────────────────────────────────

  🔴 URGENT   Prof. Martinez
             Chapter 3 feedback — revise before Thursday or we miss the committee slot
             → Action required (revision) + committee slot at risk, deadline in 3 days

  🔴 URGENT   Research Foundation
             REMINDER: Veni grant portal closes in 48 hours — action required
             → Grant deadline in 2 days, incomplete applications not reviewed

  🟡 SOON     Dr. Sarah Chen
             Postdoc position — still interested? Need to know by Friday
             → Postdoc application deadline in 4 days, competitive opportunity

  🟡 SOON     ICML 2026
             Paper submission deadline reminder — 5 days remaining
             → Submission required, deadline in 5 days

  🔵 LATER    Jamie
             Attune — reranker idea, worth discussing this week?
             → Side project discussion, no deadline pressure

  ⚪ IGNORE   Medium · 5 AI papers you should read this week
  ⚪ IGNORE   LinkedIn · You appeared in 14 searches this week
  ⚪ IGNORE   arXiv · cs.LG — 47 new submissions
  ... (and 9 more)

──────────────────────────────────────────────────────────
  25 emails  ·  2 urgent · 3 read today · 9 this week · 11 ignored
──────────────────────────────────────────────────────────
```

### `attune watch` — real-time monitoring

Runs continuously, polling every N minutes. New emails are triaged on arrival. URGENT ones trigger a desktop notification immediately.

```
  Attune watch started — polling every 5m
  Last checked: 13:11:34
  Press Ctrl+C to stop.

  [13:11:34] 2 new email(s):

    🔴 URGENT   Prof. Martinez
             Chapter 3 feedback — revise before Thursday or we miss the committee slot
             → Action required + committee slot at risk given defense in 74 days

    🔵 LATER    Jamie
             Attune — reranker idea, worth discussing this week?
             → Side project discussion, no deadline pressure

  [13:16:34] No new emails.
  [13:21:34] No new emails.
```

State is persisted in `~/.attune/state.json` — survives restarts, never re-triages a seen email.

---

## How a decision is made

A concrete trace through the system:

```
┌──────────────────────────────────────────────────────┐
│  CALENDAR CONTEXT                                    │
│                                                      │
│  Today: moderate — 3.5h blocked                      │
│    10:00 Thesis writing block                        │
│    14:00 Lab meeting                                 │
│    16:00 Supervisor check-in                         │
│                                                      │
│  Week:  Mon:L  Tue:H  Wed:M  Thu:M  Fri:L            │
│                                                      │
│  Milestones:  Veni grant deadline   →  2 days        │
│               Chapter 3 submission  →  3 days        │
│               PhD defense           → 74 days        │
└──────────────────────────────────────────────────────┘
                          +
┌──────────────────────────────────────────────────────┐
│  GOALS (from goals.yaml)                             │
│                                                      │
│  • Finishing PhD thesis — defense July 2026          │
│    Supervisor and committee feedback critical        │
│  • Applying for postdocs and grants                  │
│    Funding deadlines are urgent                      │
└──────────────────────────────────────────────────────┘
                          +
┌──────────────────────────────────────────────────────┐
│  INCOMING EMAIL                                      │
│                                                      │
│  From:    supervisor@university.edu                  │
│  Subject: Chapter 3 feedback — revise before Thu     │
│  Body:    "...fix statistical analysis in 3.2...     │
│            committee meets Friday, need it by        │
│            Thursday morning at the latest..."        │
└──────────────────────────────────────────────────────┘
                          ↓
               [ LLM triage judgment ]
                          ↓
┌──────────────────────────────────────────────────────┐
│  🔴 URGENT                                           │
│                                                      │
│  Action required (revision) + committee slot at      │
│  risk Thursday, 3 days away. Supervisor sign-off     │
│  is on the critical path to the July defense.        │
│  Delay has real cost.                                │
│                                                      │
│  → Desktop notification fired                        │
└──────────────────────────────────────────────────────┘
```

The same email with defense 8 months away and no imminent milestones → `SOON`.

---

## Evaluation

**Setup:** 25 hand-crafted mock emails covering the full label range, evaluated against ground-truth labels using `llama-3.1-8b-instant` (Groq free tier).

```
  #   Subject                                    Expected  Got      OK?
  ─── ─────────────────────────────────────────  ────────  ───────  ───
  1   Chapter 3 feedback — revise before Thu...  URGENT    URGENT   ✓
  2   Veni grant portal closes in 48 hours        URGENT    URGENT   ✓
  3   Postdoc position — need to know by Fri      SOON      SOON     ✓
  4   Thesis committee — question on methods      SOON      URGENT   ✗
  5   ICML submission deadline — 5 days           SOON      SOON     ✓
  6   Defense date confirmed — please confirm     SOON      URGENT   ✗
  7   JMLR review request — respond in 3 days     SOON      SOON     ✓
  8   Side project — reranker idea                LATER     LATER    ✓
  9   Library loan due in 5 days                  LATER     LATER    ✓
  10  Lab social — drinks Friday                  LATER     LATER    ✓
  ... (15 more)

  Overall: 15/25  (60%)

  Label     N   Correct   Precision   Recall
  ──────    ─   ───────   ─────────   ──────
  URGENT    2       2        50%       100%
  SOON      5       3       100%        60%
  LATER     9       9        53%       100%
  IGNORE    9       1       100%        11%
```

### Where it goes wrong

**SOON → URGENT (2 cases):** The model correctly identifies that the email is time-sensitive and thesis-related, but over-indexes on proximity to milestones. The prompt caps URGENT at "0–2 per day max" but the 8B model doesn't always hold that constraint.

**IGNORE → LATER (8 cases):** The model is too conservative — newsletters, Dependabot PRs, and LinkedIn notifications get `LATER` instead of `IGNORE`. The model reasons "no deadline, no action required → LATER" but doesn't make the further leap to "not worth the user's time at all."

Both are prompt-tuning issues, not architectural ones. A stronger model (Claude Haiku) handles these reliably — the failure rate drops to near zero on the same eval set.

---

## Setup

```bash
git clone https://github.com/yourusername/attune
cd attune
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

**API key** (Groq free tier works):

```bash
cp .env.example .env
# Add GROQ_API_KEY=... or ANTHROPIC_API_KEY=...
```

Switch provider:
```bash
LLM_PROVIDER=anthropic attune digest  # uses Claude Haiku
# default: Groq llama-3.1-8b-instant
```

**Goals** — edit `config/goals.yaml` in plain English.

**Try it without Google auth:**

```bash
attune digest --mock     # batch digest on 25 mock emails
attune watch --mock      # real-time mode on mock emails
```

**Against your real Gmail** (requires Google Cloud OAuth credentials in `credentials/`):

```bash
attune digest
attune watch --interval 5
```

---

## Stack

| Component | Choice | Why |
|---|---|---|
| LLM judge | Groq / Anthropic | Groq free tier for dev, Claude Haiku for production |
| Email | Gmail API (OAuth) | Read-only scope, no token stored server-side |
| Calendar | Google Calendar API | Same OAuth flow |
| CLI | Click | Clean command structure, `--mock` flag for offline dev |
| Config | PyYAML | Goals in plain English, no schema |
| State | `~/.attune/state.json` | Simple, inspectable, no database |

---

## What's next

- **Goal inference** — infer goals automatically from sent email topics, fast-reply patterns, and calendar blocks rather than requiring manual YAML
- **Multi-channel** — same triage core, Slack/Outlook connectors
- **Feedback loop** — mark a label wrong → correction stored → prompt improved over time
