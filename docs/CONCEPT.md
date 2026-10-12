# Student Life Planner: concept

## The problem
At uni, your life is spread across a timetable system, Moodle deadlines, a personal calendar, notes-app
to-do lists and your own memory. Existing planners make you do the data entry, and few of them help you
plan, e.g. *"when can I actually fit four hours for this essay around lectures?"*

## The idea
**Talk to an AI agent; it keeps one source of truth up to date; a dashboard shows the result; your phone nudges
you.** The AI is the input method and the planner; the website is mostly for glancing at.

## Design principles
1. **One server owns the data.** The dashboard, the AI and the scheduler are all clients of the same service
   layer, so they can't disagree.
2. **Trust through visibility.** Every change is logged with who made it (you or the AI) and can be undone.
   An agent editing your deadlines is only usable if mistakes are obvious and cheap to undo.
3. **AI is pull, reminders are push.** Using Claude through MCP means no API bill, but Claude only acts when
   you open a chat. So anything proactive (reminders, the morning digest, habit nudges) is rule-based and
   runs on the server.
4. **Free, open-source, self-hosted.** Python/FastAPI, SQLite, ntfy, Docker on a Pi, Cloudflare Tunnel.
5. **Import, don't retype.** Uni timetables, Moodle deadlines and Google Calendar all publish ICS feeds.

## Roadmap
| Phase | What | Status |
|---|---|---|
| 1 | Concept, skeleton, tests | Done |
| 2 | **Tasks & deadlines:** dashboard, MCP tools, activity log + undo, ntfy reminders, morning digest | Done. Use it for a week before building more |
| 3 | **Timetable & calendar:** ICS import (timetable, Moodle → tasks, Google), merged week view, `find_free_slots`, study blocks, ICS feed out, `plan_my_week` prompt | Next |
| 4 | **Habits & wellbeing:** habits, check-offs, streaks, evening nudge, `weekly_review` prompt | |
| 5 | **Deploy:** Pi + Cloudflare Tunnel + Access, MCP auth, nightly backups | |

## Ideas bank (after v1)
Money and budget (loan instalments, rent, weekly spend); two-way Google Calendar sync; a focus timer that
logs time per module; a grade tracker ("what do I need in the exam?"); a reading list; a uni admin checklist
(GP registration, council tax exemption, accommodation); shared house chores; a Telegram bot as a second chat
channel if you're happy to pay for an LLM API.
