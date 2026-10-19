# 01 · Identity and persona: one Jarvis everywhere

**What:** the workspace files that make Jarvis behave the same on Telegram, the iPhone app and the room speaker.
**Why:** "one central identity" is priority 3. It works because every interface talks to the same agent (`main`) and the same main session (`agent:main:main`). Personality and rules live in files that load on every turn.

## The files (in `~/.openclaw/workspace/`)

| File | Holds | Loaded |
|---|---|---|
| `AGENTS.md` | **Standing orders**: the programs (accountability, daily rhythm, jobs, monitoring), interruption tiers, the autonomy table, voice rules, memory rules, the time budget | Every session |
| `SOUL.md` | Personality and tone: calm, competent, British English, pushes back | Every session |
| `IDENTITY.md` | Name, vibe, emoji, wake phrase | Every session |
| `USER.md` | Your stable preferences, as dated directives (4,000-character cap) | Every session |
| `MEMORY.md` | Durable facts tagged `[stated]` / `[inferred]` | Main session |
| `tasks.md` | General to-dos (homework first) | When the agent reads it |

Templates for all of these are in `workspace/`.

## Standing orders: how Jarvis acts without being asked

OpenClaw's **standing orders** pattern: `AGENTS.md` grants Jarvis permanent authority for named *programs*. Each program has an authority, triggers, approval gates and escalation rules. **Automations** decide *when* a program runs, and the automation message just says "follow the X skill / standing orders". Keep the detail in one place.

The four programs in the template:

1. **Accountability loop:** commitments, the ladder, snooze/cancel rules.
2. **Daily rhythm:** briefing, evening check-in, end of day, weekly review.
3. **Background jobs:** research that survives you leaving.
4. **Monitoring:** server health; restart the voice daemon; escalate on repeats.

Every program follows **Execute → Verify → Report**. "I'll do that" doesn't count.

## Interruption tiers (how "10/10 proactive" doesn't become annoying)

| Tier | Examples | Delivery |
|---|---|---|
| Interrupt now | Calendar clash, deadline < 24 h, overdue commitment | Spoken if you're home **and** sent on Telegram; Telegram only if you're away |
| Next briefing | Research done, news, project updates | Morning briefing or end-of-day summary |
| Log only | Routine monitoring | Daily log and dashboard |

Quiet hours are 23:30–07:00: no voice, and Telegram only for interrupt-now items.

## Autonomy

The template's table splits actions into "do automatically" and "ask first". Approvals arrive as **Telegram inline buttons** or **iOS app approval cards**. Voice can never approve anything, so someone shouting in your room can't trigger an external action.

## Personality tuning

The spec asks for 6–7/10 personality. If Jarvis is too chatty, add a line under *Voice and tone* in `SOUL.md` ("Max two sentences unless asked"). If it's too flat, allow "the occasional dry line". Change one thing at a time and give it a few days.

## Verify

- [ ] "What are your standing orders?" → it lists the four programs
- [ ] Ask on Telegram, then follow up by voice ("what did I just ask you?") → same context
- [ ] "Delete my calendar" → it asks for approval instead of acting
