---
name: end-of-day-summary
description: Evening review at 22:00 - summarise completed, snoozed and cancelled commitments, raise cancel reasons, and plan tomorrow.
metadata: { "openclaw": { "emoji": "🌙", "requires": { "bins": ["python3"] } } }
---

# End-of-day summary

## Gather

- `python3 skills/commitments/scripts/commitments.py summary`: today's
  done / cancelled / snoozed / still-open commitments.
- Today's daily log: the debrief and any jobs that finished.
- Tomorrow's calendar via `gog`, plus `tasks.md` items due tomorrow.

## Write (Telegram, about 120 words)

```
Today: ✅ 2 done · ⏸ 1 snoozed · ✖ 1 cancelled
✅ Maths past paper
⏸ Econ essay plan → tomorrow 17:00
✖ CS write-up: "teacher extended it". Fair enough?
Still open: ...
Tomorrow: college 09:00 (leave 08:25), free 15:30–18:00.
Suggested: stats revision 16:00–17:00. Block it?
```

- Raise **every cancel reason**, briefly and without judgement. Ask a
  question only if the reason looks like avoidance (e.g. the same task
  cancelled twice this week).
- Still-open commitments that are past due: ask once whether to move them
  to tomorrow (snooze with a time) or cancel them (with a reason).
- If Taylor agrees to a suggested block, use `revision-planner`.
- Append a `## End of day` section with the same summary to today's daily
  log, so the weekly review can count it.
