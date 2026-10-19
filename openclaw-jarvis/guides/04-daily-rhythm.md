# 04 · Daily rhythm: morning, day, evening, Sunday

**What:** the scheduled touchpoints that make Jarvis feel "always on".
**How:** each touchpoint is an **automation** (when) that tells Jarvis to follow a **skill** (what), inside the main session so your replies keep their context. All times are Europe/London.

| Time | Automation | Skill | Notes |
|---|---|---|---|
| 07:00 Mon–Fri, 09:00 Sat–Sun | Morning briefing | `morning-briefing` | Short version on Telegram, offers the full one. Saying "Hey Jarvis, good morning" gets the spoken version |
| Every 5 min (silent unless due) | Commitment watcher | `commitment-checkin` | Guide 03 |
| Arrive home (iOS) / 19:00 fallback | Evening check-in | `evening-checkin` | Debrief → tonight's one priority → commitment with a time |
| 22:00 | End-of-day summary | `end-of-day-summary` | Done / snoozed / cancelled (reasons raised), tomorrow's plan |
| Sun 17:00 | Memory review | `memory-review` | Confirm, fix or delete `[inferred]` memories |
| Sun 18:00 | Weekly review | `weekly-review` | Completion rate, patterns, next week, revision plan |

## Install

```bash
cd ~/openclaw-jarvis
export TELEGRAM_CHAT_ID=<your numeric id>
bash automations/setup-automations.sh
openclaw automations list --all
```

The script is safe to re-run: each job has a `--declaration-key`, so it updates the job instead of duplicating it. To change a time later, edit the script and re-run it, or use `openclaw automations edit <id> --cron "15 7 * * 1-5"`.

## The ideal morning (from your spec), and how it maps

> **You:** "Hey Jarvis, good morning."
> **Jarvis:** "Morning, Taylor. It's 06:48, Tuesday. Full briefing or just the essentials?"

- The wake word goes to the voice daemon (guide 11), then into the main session. The `morning-briefing` skill asks "full or essentials".
- Follow-ups work because it's one session: "Did I finish that homework?" (it reads `tasks.md`), "Save that" (`MEMORY.md`), "Block Thursday evening for revision" (`revision-planner`, which needs your yes before writing to the calendar).
- If the 07:00 briefing has already gone to Telegram, the spoken one is the full version. The skill checks `briefing: sent` in the daily log, so you never get the same thing twice.

## During the day

- Jarvis messages only for **interrupt now** items (guide 08). Everything else waits for the briefing or the end-of-day summary.
- Background research keeps running after you leave (guide 07).

## Verify

- [ ] `openclaw automations list --all` shows the 10 Jarvis jobs (plus OpenClaw's own heartbeat/dreaming entries)
- [ ] `openclaw automations run <morning-id>` → a short briefing arrives on Telegram
- [ ] At 22:00 the summary arrives and asks about any cancel reasons
- [ ] `openclaw automations runs <id>` shows `ok` for each job after its first day
