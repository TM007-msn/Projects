---
name: research-job
description: Run "research X and get back to me" as a background job that survives the chat ending - save results to research/ and notify when done.
metadata: { "openclaw": { "emoji": "🔎" } }
---

# Research job

Use this when Taylor asks for research that takes more than a quick answer:
product comparisons, hardware research, "find out about…", "keep an eye on…".

## Start

1. Restate the question in one line and agree the output, e.g. "a
   comparison table plus a recommendation, about 300 words". Ask only if
   it's genuinely unclear.
2. Add a line to `research/JOBS.md`:
   `- [running] 2026-10-19 18:40 · <slug> · <question>`
3. Spawn a **detached sub-agent** with the `researcher` agent (it has web
   tools only, with no access to email, calendar or private files). Give it
   the question, the expected output, and the path to write to:
   `research/YYYY-MM-DD-<slug>.md`.
4. Tell Taylor it's running and roughly how long it'll take. Then carry on
   with the conversation; don't wait.

## When the sub-agent finishes

1. Check that the file exists and actually answers the question. If it
   doesn't, retry once with a sharper brief.
2. Update `research/JOBS.md` to `[done]` (or `[failed: reason]`).
3. Notify by **tier** (AGENTS.md → Interruption tiers):
   - Taylor said "tell me when it's done", or it's time-sensitive: **interrupt
     now**. Send a 3-line summary and the file name.
   - Otherwise: **next briefing**. Leave it for the morning briefing or the
     end-of-day summary.
4. Add a one-line pointer to MEMORY.md → Research, so it can be found later.

## Rules

- Prefer primary sources, and show prices in £ for UK availability.
- If two sources disagree, say so; don't pick one silently.
- Several jobs may run at once. Each one gets its own line in JOBS.md.
