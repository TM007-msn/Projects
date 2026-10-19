# Automations (cron jobs)

Create or update them all with:

```bash
export TELEGRAM_CHAT_ID=<your numeric Telegram user ID>
bash automations/setup-automations.sh      # safe to re-run (each job has a --declaration-key)
openclaw automations list --all
```

All times are **Europe/London**. "Main" session means the job runs inside Jarvis's single conversation (shared with Telegram and the room speaker), so your replies keep their context.

| Job | Schedule | Session | Payload | Delivers | Tier / notes |
|---|---|---|---|---|---|
| Morning briefing (weekdays) | `0 7 * * 1-5` | main | system event → `morning-briefing` | Telegram (+ spoken line if home) | Short briefing; full on request |
| Morning briefing (weekend) | `0 9 * * 0,6` | main | system event → `morning-briefing` | Telegram (+ voice) | |
| Commitment watcher | every 5 min + `commitment-watcher.js` | main | system event → `commitment-checkin` | Voice if home, always Telegram | Trigger script reads the ledger with **no model call**; fires only when a ladder stage is due; retries after 15 min if a send failed |
| Evening check-in fallback | `0 19 * * *` | main | system event → `evening-checkin` | Telegram (+ voice) | Skipped if the arrive-home shortcut already ran it |
| End-of-day summary | `0 22 * * *` | main | system event → `end-of-day-summary` | Telegram (+ voice) | Raises cancel reasons; plans tomorrow |
| Memory review | `0 17 * * 0` | main | system event → `memory-review` | Telegram only | Never spoken aloud |
| Weekly review | `0 18 * * 0` | main | system event → `weekly-review` | Telegram (+ voice) | Stats, patterns, revision plan |
| Server health | every 30 min | isolated | **command** `health.sh` | Telegram, only on problems | No model call; prints `NO_REPLY` when healthy |
| Nightly backup | `30 2 * * *` | isolated | **command** `nightly-backup.sh` | Telegram, only on failure | `openclaw backup` offsite + workspace git push |
| Update & security check | `0 9 * * 1` | isolated | agent turn (Sonnet, light context, exec+read only) | Telegram, only if action needed | `openclaw update status` + `openclaw security audit` |

Not created by this script, but present in `openclaw automations list --all`:
- `heartbeat-main` / `heartbeat-researcher`: OpenClaw's system heartbeat jobs, **disabled** (`heartbeat.every: "0m"`). See guide 08 for turning them on in Phase 3.
- `Memory Dreaming Promotion` (03:00): OpenClaw's built-in memory consolidation (guide 06).

## Everyday commands

```bash
openclaw automations list --all                 # everything, including disabled
openclaw automations run <id>                   # run now (ignores the trigger script)
openclaw automations runs <id> --limit 10       # history, including triggerFired / errors
openclaw automations edit <id> --cron "15 7 * * 1-5" --tz Europe/London
openclaw automations disable <id>               # pause without deleting
```

Or just tell Jarvis on Telegram: "move the morning briefing to 07:15", "pause the weekly review this week". As the owner you can manage automations conversationally.

## Tested

Run against a real OpenClaw 2026.10.5 Gateway on 19/10/2026:
- all 10 jobs created with `Europe/London` schedules, agent `main`
- re-running the script three times made no duplicates
- the watcher's trigger script fired (`triggerFired: true`) for a due commitment, then stayed quiet for 5 evaluations after the nudge was recorded (no model runs)
