# 05 · Calendar and tasks

**What:** Jarvis reads your calendar, finds free time, blocks revision, and tracks tasks.
**Recommendation:** **Google Calendar via the bundled `gog` skill**, commitments in `state/commitments.json`, to-dos in `tasks.md`.

## Why Google rather than self-hosted CalDAV (Radicale)

You said you weren't attached either way, so this is about what fits an OptiPlex-only setup best:

| | Google Calendar + `gog` | Radicale on the OptiPlex |
|---|---|---|
| Works with Jarvis today | ✅ Bundled skill, a few minutes of OAuth | ❌ Needs a custom skill to be written |
| iPhone sync | Native (Settings → Calendar → Accounts → Google) | Native CalDAV, but **only while Tailscale is connected** |
| College timetable (ICS) | Subscribe once in Google Calendar | Needs a separate sync job |
| Maintenance | None | Another service to keep running, back up and secure |
| Privacy | Google holds the events | Fully yours |

Calendar 10/10 and reliability 2/12 beat the privacy gain here. Once the local-AI box arrives, migrating to Radicale is a contained job (export ICS, import, swap the skill) if privacy becomes the priority.

**Why not Google Tasks for to-dos?** `gog` doesn't support Tasks, and the accountability loop needs data no task app has (escalation stage, snooze history, your quoted words). So: commitments go in the ledger, and light to-dos go in a Markdown list that both you and Jarvis can read.

## Setup: `gog` on a headless OptiPlex

1. Install: `brew install gogcli` (Linuxbrew) or follow the instructions at https://gogcli.sh.
2. In Google Cloud Console, create a project → enable the **Calendar API** (and Gmail later, for guide 08) → create an OAuth client (type: Desktop) → download `client_secret.json` to the OptiPlex.
3. Authorise, using the headless flow (it prints a URL to open on your phone or laptop):
   ```bash
   gog auth credentials ~/client_secret.json
   gog auth add <you>@gmail.com --services calendar
   gog auth list
   rm ~/client_secret.json
   ```
4. Timetable: in Google Calendar on the web, go to Other calendars → **From URL** and paste the college timetable ICS link. Note its calendar ID (Settings → the calendar → Integrate → Calendar ID).
5. Put the IDs in `AGENTS.md` → Tools (`primary`, and the timetable ID).
6. Test it on Telegram: "What's on tomorrow?", then "When am I free on Thursday after 15:00?"

## Revision blocking

The `revision-planner` skill finds gaps of 45+ minutes between 07:30 and 22:00 (with 15-minute buffers), proposes `Revision: <subject> – <topic>` blocks weighted towards weak topics and the nearest exams, and **only writes after you say yes**. "Block Thursday evening for revision" counts as that yes for that one block. Blocks use colour 9 so they stand out.

Tip: put your weak topics and exam dates in `MEMORY.md` → *Revision*. Better input gives better plans.

## Tasks (`tasks.md`)

```markdown
## Homework
- [ ] Maths Ex 4B Q1–12 · due 22/10 · maths
- [~] Econ essay plan · due 24/10 · econ        ← [~] = started
- [x] CS trace tables worksheet · due 18/10 · cs
```

The spec's "distinguish started from completed work" maps to `[ ]` / `[~]` / `[x]`. Jarvis adds tasks when you mention them ("I've got Ex 4B for Wednesday"), ticks them when you say they're done, and surfaces overdue ones in the briefing. A task that needs a definite time tonight becomes a **commitment** instead.

## Verify

- [ ] "What's on tomorrow?" includes timetable lessons
- [ ] "Find me two revision slots this week" → a proposal, and nothing written yet
- [ ] "Yes, add them" → the events appear on your iPhone calendar within a minute
- [ ] "I've got Ex 4B due Wednesday" → a line appears in `tasks.md`
