# 08 · Proactivity without overwhelm

**What:** Jarvis notices things and acts, without being prompted, through the right channel at the right time.
**Why:** proactivity is priority 1. Your spec resolves "10/10 proactive" vs "don't overwhelm me" with **interruption tiers** (in `AGENTS.md`).

## The building blocks, from cheapest to most expensive

| Mechanism | Use it for | Cost |
|---|---|---|
| **Command automation** | Deterministic checks (server health, backups) | No model call; prints `NO_REPLY` when quiet |
| **Condition watcher** (`--trigger-script`) | "Tell me when X changes" (commitments, prices, CI, email count) | Script runs free; the model only wakes when it fires |
| **Scheduled automation** | Fixed times (briefing, reviews) | One model turn per run |
| **Standing intent** | "When X comes up, remind me of Y" | No timer; matched by keywords on your messages |
| **Heartbeat** | Open-ended "anything need attention?" polling | A model turn every interval; **off in Phase 1** |

Start with scheduled triggers, then add event triggers. This is your spec's own sequencing, and it's what `setup-automations.sh` does.

## Standing intents (event-based reminders)

Just say it on Telegram:

> "When I mention the CS NEA, remind me the write-up deadline is 14/02."

Jarvis stores it with the `intent` tool (owner-only, which is why `ownerAllowFrom` matters). It fires at most 3 times, with a 24-hour cooldown, and expires after 90 days by default. It costs nothing until it matches.

## Why the heartbeat is off for now

The heartbeat is a periodic main-session turn. Without a checklist it mostly replies "nothing to do", but each run still costs tokens, and running it hourly with full context could eat most of your £10–30 budget. Every proactive job in Phase 1 is an explicit automation instead.

**Phase 3:** turn it on cheaply for email triage:

```json5
heartbeat: { every: "2h", lightContext: true, isolatedSession: true,
             activeHours: { start: "07:00", end: "23:00" } }
```

Then give it a small checklist:
`openclaw cron scratch <heartbeat-job-id> --set "Check Gmail for anything from college or deadlines in the last 2h; interrupt-now only if action is needed today, otherwise NO_REPLY."`

## Event triggers to add later (Phase 3)

- **Email:** Gmail Pub/Sub → `hooks.presets: ["gmail"]`. Each new email wakes a restricted reader agent, and only important ones reach you. See the OpenClaw "Gmail PubSub" automation docs, which recommend a restricted reader agent.
- **Calendar changes:** a condition watcher every 15 minutes comparing `gog calendar events` against the last snapshot, firing on changes within the next 48 hours ("interrupt now" if it clashes).

## Verify

- [ ] Over a normal day you get roughly: the briefing, 1–3 nudges, the evening check-in and the summary. Not more.
- [ ] A standing intent fires when its keyword comes up, and not again within 24 hours
- [ ] Nothing speaks in your room between 23:30 and 07:00
