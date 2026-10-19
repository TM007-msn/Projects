---
name: revision-planner
description: Find free calendar slots and propose or block revision sessions on Google Calendar (asks before writing). Use for "block Thursday evening for revision".
metadata: { "openclaw": { "emoji": "📚", "requires": { "bins": ["gog"] } } }
---

# Revision planner

## Find free time

1. Read events for the requested range from both the primary calendar and
   the timetable calendar:
   `gog calendar events <calendarId> --from <iso> --to <iso>` (calendar IDs are
   in AGENTS.md → Tools).
2. Free slot = a gap of at least 45 minutes between 07:30 and 22:00, with
   15-minute buffers either side of events, and outside sleep and meal times
   (USER.md).

## Propose

- Suggest blocks of 45–90 minutes, named `Revision: <subject> – <topic>`.
  Weight them towards weak topics (MEMORY.md → Revision) and the nearest
  exam or deadline.
- Show the proposal as a short list and ask: "Add these to your calendar?"

## Write (only after an explicit yes)

```bash
gog calendar create <primaryCalendarId> --summary "Revision: Maths – Hypothesis testing" \
  --from 2026-10-22T16:00:00+01:00 --to 2026-10-22T17:00:00+01:00 --event-color 9
```

- Use colour 9 (blueberry) for every revision block, so they're easy to spot.
- If the user said "block Thursday evening", that is the approval for that
  one block. Confirm what you created in one line.
- Never move or delete existing events without asking.
- Optionally turn a block into a commitment (ask first) so the ladder
  applies to it.
