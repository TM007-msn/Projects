---
name: morning-briefing
description: Build Taylor's morning briefing (full or short): weather, calendar, leaving time, tasks, homework, overnight jobs, news and revision slots.
metadata: { "openclaw": { "emoji": "🌅" } }
---

# Morning briefing

Runs from the 07:00 automation, or when Taylor says "good morning" or asks
for the briefing. On voice, first ask: "Full briefing or just the essentials?"
Scheduled runs send the **short** version to Telegram and offer the full one.

## Gather (in parallel where possible)

1. **Date and time.** Say them naturally ("Tuesday 20/10, 06:48").
2. **Weather.** Use the `weather` skill for the home town (see USER.md) and turn
   it into practical advice: coat or umbrella, leave early if it's icy or wet.
3. **Calendar.** Use the `gog` skill to list today's events from the primary
   calendar and the college timetable calendar. Work out the
   **leaving time**: first in-person event minus travel time (USER.md), minus
   a 10-minute buffer.
4. **Commitments and tasks.** Run
   `python3 skills/commitments/scripts/commitments.py list` for open
   commitments. Read `tasks.md` and flag anything due today or overdue, with
   homework first.
5. **Overnight jobs.** Look in `research/` and today's daily log for jobs that
   finished since yesterday evening. Give one line each.
6. **Server status.** Mention it only if something's wrong (see the latest
   server-health output).
7. **News and interests.** Give at most three items relevant to Taylor's
   interests (USER.md). Skip anything generic.
8. **Free time.** Suggest one or two revision slots from today's calendar
   gaps, linked to the weakest topic in `MEMORY.md` → Revision.

## Shape

- **Short:** 5–7 lines covering the time, weather advice, first event and
  leaving time, the top two tasks, and anything urgent.
- **Full:** short version first, then sections for calendar, tasks, jobs,
  news and suggestions. Stay under about 250 words. For voice, write it to
  be spoken: no tables or URLs, and numbers said naturally.
- End with one question that invites a follow-up, e.g. "Want me to block
  16:00–17:00 for the stats revision?"

## Don't

- Don't read out empty sections ("No news today").
- Don't send anything at all if a briefing has already gone out today
  (check today's daily log for `briefing: sent`). Otherwise log
  `briefing: sent HH:MM` when done.
