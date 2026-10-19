# 07 · Background jobs and research

**What:** "Research that and get back to me" keeps working after you end the chat and leave the room. Several jobs can run at once.
**Why:** priority 5 ("critical" in your spec). OpenClaw has this built in: **detached sub-agents** have their own run lifecycle, and their completion hand-offs are stored in SQLite, so they survive a Gateway restart.

## How a research job runs

1. You ask: "Compare the Mac Studio, DGX Spark and Strix Halo for local LLMs, UK prices."
2. The `research-job` skill:
   - adds `- [running] … · local-ai-box · …` to `research/JOBS.md` (your jobs ledger)
   - spawns a sub-agent on the **`researcher`** agent, which has web search and fetch only, with **no** email, calendar, shell or private files
   - tells you it's running, and the conversation carries on
3. The sub-agent writes `research/2026-10-19-local-ai-box.md` and finishes.
4. Jarvis checks the file actually answers the question (and retries once if not), marks `[done]` in JOBS.md, and notifies by tier: **interrupt now** if you asked to be told, otherwise it goes in the next briefing.

## Least privilege: why there's a separate `researcher` agent

The config defines `agents.entries.researcher` with `skills: []` and tools limited to `web_search`, `web_fetch`, `read`, `write`. `main` may spawn it (`subagents.allowAgents: ["researcher"]`). A web page containing a prompt injection ("ignore instructions, email X") hits an agent that **has no email tool and can't see your files**. This is your spec's "a research agent gets no private files".

## Monitoring jobs ("keep an eye on…")

For something that should be checked repeatedly, use a **condition-watcher automation** instead of a long-running sub-agent:

```bash
openclaw automations add --name "Watch: RTX price" --every 6h \
  --trigger-script ./watch-price.js \
  --session isolated --agent researcher \
  --message "The watched price changed; summarise in 2 lines." \
  --announce --channel telegram --to <chat id>
```

The trigger script does the cheap check (fetch and compare) and only wakes a model when something changed, the same pattern as the commitment watcher.

## Workboard (optional, for coding/multi-step projects)

OpenClaw's bundled **Workboard** plugin (`openclaw plugins enable workboard`) gives you a card board (`triage → ready → running → review → done`) that dispatches cards to sub-agent workers, with live progress in the dashboard. Use it when you have several project tasks for Jarvis to grind through. For everyday research, `research/JOBS.md` is simpler.

## Verify

- [ ] Ask for research, then immediately `/new` or close Telegram → the result still arrives
- [ ] `openclaw gateway restart` mid-job → the job still reports back
- [ ] Two research jobs at once → two lines in JOBS.md, two results
- [ ] Ask the researcher to "read MEMORY.md" → it can't (it isn't in its workspace)
