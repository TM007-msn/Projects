---
name: evening-checkin
description: Run the evening debrief when Taylor gets home: log how the day went, then turn tonight's one priority into a timed commitment.
metadata: { "openclaw": { "emoji": "🌆", "requires": { "bins": ["python3"] } } }
---

# Evening check-in

Triggered by the "arrive home" webhook, the 19:00 fallback automation, or
Taylor saying something like "I'm back".

**First,** check today's daily log (`memory/YYYY-MM-DD.md`) for
`evening-checkin: done`. If it's there, stop: the debrief has already
happened today. If the 19:00 fallback fires and presence is `away`, send one
Telegram message ("How did today go? Tell me when you're back") and stop.

## Flow

1. **Greet.** Keep it to one line, and make it relevant. Use `room-speak` if
   presence is `home`.
2. **Debrief.** Ask "How did today go?" Let Taylor talk. Then write a dated
   entry in today's daily log:
   ```markdown
   ## Debrief HH:MM
   - Done: ...
   - Not done: ...
   - Notes: ...   (mood, blockers, anything to remember)
   ```
   Durable facts (a new deadline, a changed timetable) also go to MEMORY.md,
   tagged `[stated]`.
3. **Tonight's priority.** Ask: "What's the one thing that matters tonight?"
   If Taylor offers several, ask them to pick one. If nothing is offered,
   suggest one from overdue tasks or the revision plan.
4. **Make it a commitment.** Get a time ("By when?") and add it:
   `python3 skills/commitments/scripts/commitments.py add --what "..." --due HH:MM --quote "<their words>"`.
   Confirm it back in one line: "Locked in: maths past paper by 20:00. I'll
   check in at 19:30."
5. **Log it.** Write `evening-checkin: done HH:MM` to today's daily log.

## Tone

Calm, interested, brief. Push back if the plan is unrealistic, e.g. "That's
three hours of work and it's 21:30. Pick the part that matters most."
