---
name: weekly-review
description: Sunday weekly review - commitment follow-through stats, patterns, next week's calendar and a proposed revision plan.
metadata: { "openclaw": { "emoji": "📊", "requires": { "bins": ["python3"] } } }
---

# Weekly review (Sunday 18:00)

1. **Follow-through.** For each of the last 7 days, run
   `python3 skills/commitments/scripts/commitments.py summary --date YYYY-MM-DD`.
   Report done, snoozed and cancelled counts and the completion rate,
   compared with last week (in MEMORY.md → Weekly stats).
2. **Patterns.** Name at most two, plainly. For example: "Snoozes cluster
   after 21:00", "Econ tasks get cancelled most". Keep it factual. Save
   any pattern to MEMORY.md tagged `[inferred]`, so Taylor can confirm or
   delete it in the memory review.
3. **Next week.** List deadlines and fixed events from `gog` and `tasks.md`.
   Find the free blocks.
4. **Revision plan.** Propose 3–6 blocks, weighted towards weak topics
   (MEMORY.md → Revision) and the nearest exams. Ask before writing any of
   them to the calendar (see `revision-planner`).
5. **Build time check.** If Jarvis build work this week went over the cap
   in AGENTS.md, say so.
6. Save the stats line to MEMORY.md → Weekly stats.

Keep the message under about 200 words, with the stats first and one clear
question at the end.
