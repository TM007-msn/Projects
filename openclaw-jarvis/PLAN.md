# Jarvis: the OpenClaw plan (v3)

*19/10/2026 · supersedes Jarvis Spec v2 (28/09/2026)*

## What Jarvis is

One proactive personal assistant, secretary and accountability partner that lives in your room, phone and PC, **holds you to what you say you'll do**, and runs work in the background. It isn't a chatbot: it remembers useful context, uses tools, and contacts you when something matters.

> "A reliable, secure, persistent and proactive personal AI agent that knows my context, remembers me, runs jobs independently, communicates naturally, and exists as one consistent Jarvis identity across my room, phone and PC."

**The test for every feature: does it help you get the right work done?** You're in a resit year, so revision beats building Jarvis. Build time is capped at **3 hours a week**.

## What changed since Spec v2

| Spec v2 assumed | Now | Effect on the plan |
|---|---|---|
| Mac mini M5 Pro 48GB for voice, iMessage and local AI | **OptiPlex only for a few months.** A 128GB box (Mac Studio / DGX Spark / Strix Halo) is undecided | Voice runs on the OptiPlex now (Python daemon). Local AI is gated (guide 12) |
| Build a SwiftUI iPhone app (Phase 4) | The **official OpenClaw iOS app** has push, approvals, Talk voice, Siri shortcut, Watch | Phase 4 dropped; you get it on day one |
| iMessage via a bridge | BlueBubbles removed; iMessage needs a signed-in Mac + `imsg` | **Telegram + iOS app**; iMessage only if a Mac Studio arrives |
| Radicale CalDAV | No bundled CalDAV skill; OptiPlex-only | **Google Calendar via `gog`**; Radicale is a later option |
| OpenClaw ≥ v2026.1.29 | Current release is **v2026.10.5**: `cron` → `automations`, heartbeat tasks moved to automations, condition watchers, dashboards, standing intents, dreaming, `openclaw backup` | Everything here targets 2026.10.5 |
| TRMNL shows the briefing | TRMNL already runs from its own website plugins | No integration |

## Priorities (unchanged)

1 Proactivity · 2 Reliability · 3 One identity · 4 Persistent memory · 5 Background jobs · 6 Calendar/tasks · 7 Natural voice · 8 Research/web · 9 Security/privacy · 10 Local files/notes · 11 Local AI · 12 Raw hardware

## Decisions

| Area | Decision | Guide |
|---|---|---|
| Agent platform | OpenClaw 2026.10.5 on the OptiPlex ("Ace" becomes "Jarvis") | 00 |
| Always-on host | Dell OptiPlex 7060 Micro (Ubuntu), systemd user services, Tailscale-only | 00, 09 |
| Phone channel | **Telegram** (chat, buttons, voice notes, approvals) + **OpenClaw iOS app** (push, approvals, Talk) | 02 |
| Room voice | **Python daemon on the OptiPlex**: openWakeWord "hey jarvis" → faster-whisper → Gateway → Piper; ReSpeaker XVF3800 + powered speaker on its 3.5mm out | 11 |
| Calendar | Google Calendar via bundled `gog`; college timetable subscribed as ICS | 05 |
| Commitments | `state/commitments.json`, managed only by `commitments.py` (rules enforced in code) | 03 |
| To-dos | `tasks.md` (`[ ]` / `[~]` / `[x]`) | 05 |
| Memory | Markdown: `USER.md` directives, `MEMORY.md` tagged `[stated]` / `[inferred]`, daily logs; Sunday review | 06 |
| Background jobs | Detached sub-agents on a **web-only `researcher` agent**; ledger `research/JOBS.md` | 07 |
| Proactivity | Explicit automations + condition watchers + standing intents; **heartbeat off** in Phase 1 | 04, 08 |
| Models | Sonnet everyday, Opus on demand, GPT fallback; local models after the box | 00, 12 |
| Dashboard | OpenClaw Control UI (+ `/controlui` in Telegram), pinned *Today* report | 10 |
| Local AI box | **Don't buy yet.** If you buy: Mac Studio for Jarvis fit, Strix Halo for value, skip the DGX Spark | 12 |

## Architecture

```
                 ┌────────────── interfaces (all one identity) ──────────────┐
  Room: XVF3800 mic + speaker      Phone: Telegram + OpenClaw iOS app     PC: browser / node host
        │  jarvis_voice.py                │                                     │
        │  /v1/chat/completions           │                                     │
        ▼  session agent:main:main        ▼                                     ▼
 ┌──────────────────────────── OpenClaw Gateway on the OptiPlex ─────────────────────────────┐
 │ agent "main" = Jarvis (AGENTS/SOUL/USER/MEMORY.md)   one main session for every channel    │
 │ automations: briefing · commitment watcher · check-ins · reviews · health · backup        │
 │ hooks: iOS arrive/leave → presence      approvals: Telegram buttons / iOS cards            │
 │ agent "researcher" (web only, no files/email/shell) ← detached research sub-agents         │
 └──────────────┬─────────────────────────────┬──────────────────────────────┬───────────────┘
                ▼                             ▼                              ▼
   Workspace (git, private):          Tools: gog (Calendar),          Models: Claude (primary),
   commitments.json, tasks.md,        weather, web search/fetch,      GPT (fallback); local
   memory/, research/, skills/        voice /say, presence            models later (guide 12)
```

## Roadmap

Each phase starts only when the previous one has earned it.

### Phase 1: Foundations, the accountability loop, room voice (now, OptiPlex)

| Week (3 h each) | Do | Guides |
|---|---|---|
| 1 | Back up and upgrade to 2026.10.5, systemd, Tailscale, secrets, Ace → Jarvis, workspace files, **restore test** | 00, 01, 09 |
| 2 | Telegram hardening, iOS app, presence shortcuts, **commitments + automations** | 02, 03, 04 |
| 3 | Google Calendar + timetable, tasks, memory habits, research jobs | 05, 06, 07 |
| 4 | **Room voice** (buy a ~£30 powered AUX speaker), then tune latency | 11 |

**Move on when:** you've used it daily for 2 weeks, and the weekly review shows commitments actually getting done.

### Phase 2: Integration (once the core loop is stable)

Email triggers (Gmail Pub/Sub → restricted reader), calendar-change watcher, cheap heartbeat for triage, Obsidian, Windows PC as a node, pinned dashboard, tidy desk unit. Guides 08, 10, 13.

**Move on when:** the core loop has run for a month without SSH firefighting.

### Phase 3: Local AI box (gated; earliest after exams, summer 2027)

Buy only if the gate in guide 12 passes. Then: local models, private behavioural analysis, dreaming on the local model, faster voice (or native macOS Voice Wake on a Mac Studio), offline fallback, optional iMessage.

### ~~Phase 4: Build a native app~~

Replaced by the official OpenClaw iOS app. Revisit only as a portfolio project, if ever.

## Must-have checklist

| Must-have | How it's met | Phase | Status |
|---|---|---|---|
| Accountability loop (commitments, check-ins, escalation) | `commitments` + `commitment-checkin` skills, watcher automation | 1 | Built, tested |
| One central identity | One agent, one main session across Telegram, voice and iOS (`dmScope: main`, voice session key) | 1 | Built |
| Shared memory everywhere | Workspace Markdown, loaded in every channel | 1 | Built |
| Highly proactive behaviour | Automations, interruption tiers, standing intents | 1 | Built |
| Persistent background jobs | Detached sub-agents (survive restarts), `research-job` skill | 1 | Built |
| Multiple concurrent tasks | Sub-agents run in parallel; one JOBS.md line each | 1 | Built |
| Calendar awareness | `gog` + timetable ICS; briefing; `revision-planner` | 1 | Needs gog OAuth |
| Task and reminder management | `tasks.md` + commitments ledger | 1 | Built |
| Natural far-field voice | OptiPlex voice daemon, XVF3800 echo cancellation, barge-in | 1 | Built; needs on-device test |
| Phone and remote messaging | Telegram + iOS app | 1 | Config ready |
| Long-term editable memory | Tagged MEMORY.md, git history, Sunday review, `memory forget` | 1 | Built |
| Secure inferred behavioural memory | `[inferred]` tags + review now; local-only analysis after the box | 1 → 3 | Partly |
| Web research | `researcher` agent (web only) | 1 | Built |
| Local file access | Workspace now; Obsidian / PC node later | 2 | Planned |
| Reliable 24/7 operation | systemd, health checks, failure alerts, nightly backups, restore test | 1 | Built |
| Safe automatic actions | Autonomy table in AGENTS.md | 1 | Built |
| Approval for sensitive actions | Exec approvals via Telegram buttons / iOS cards; voice can't approve | 1 | Config ready |
| Small local AI model | After the box | 3 | Gated |
| Cloud AI escalation | Sonnet → Opus on demand, GPT fallback | 1 | Done |
| Offline fallback | Voice: time/date + "can't reach" message now; full offline after the box | 1 → 3 | Partly |
| Morning briefing | `morning-briefing` + 07:00/09:00 automations | 1 | Built |
| Evening check-in | `evening-checkin` + arrive-home hook + 19:00 fallback | 1 | Built |
| End-of-day summary | `end-of-day-summary` + 22:00 automation | 1 | Built |
| Friendly but professional personality | SOUL.md | 1 | Built |
| Attractive, finished physical device | Tidy desk unit: mic + speaker, cables to the OptiPlex | 2 | Planned |

## Costs

- **Spent so far:** £0 (OptiPlex, mic array, iPhone already owned).
- **Phase 1:** a powered speaker with AUX input, about **£20–50**.
- **Running:** cloud models **£10–30/month** (heartbeat off; watcher quiet ticks are free); electricity for one always-on mini PC.
- **Phase 3 box:** £4,000–5,500 at October 2026 prices. Decide later.

## Risks and open questions

- **Resit year time:** 3 h/week cap, written into AGENTS.md so Jarvis itself flags overruns.
- **Nag tuning:** the ladder stops at firm. Tune offsets only after 2 weeks of weekly-review data.
- **Voice latency on CPU:** expect 3–5 s. Measure with the daemon's timings; `base.en` is the first lever.
- **OpenClaw security history:** stay current (weekly check), tailnet only, audit community skills.
- **Google holds calendar data:** accepted for reliability; Radicale migration path documented.
- **Hardware prices:** volatile in 2026. Re-check before any purchase.
- **XVF3800 specifics:** confirm the USB-audio firmware and the mute control on your board revision.
