# 10 · Dashboard ("Mission Control")

**What:** one place to see commitments, jobs, memory and automations, and edit them.
**How:** OpenClaw's **Control UI** already does most of this. Open it in a browser over Tailscale, or inside Telegram with `/controlui`.

| You want to see | Where |
|---|---|
| Edit memory and persona files | Control UI → Settings → Agents → Files (AGENTS.md, MEMORY.md, USER.md…) |
| Automations, next run times, run history and transcripts | Control UI → **Automations** |
| Background jobs | `research/JOBS.md` (Files), or Workboard if you enable it |
| Main conversation (all channels) | Control UI → **Home** |
| Cost | `/usage cost` in chat |

## A pinned "Today" board

Session dashboards let Jarvis pin native reports (tables, metrics, links) to the Control UI. Ask once:

> "Pin a dashboard report called *Today* showing open commitments (with stage), today's tasks and running research jobs. Update it whenever any of those change."

Jarvis uses the `show_widget` tool with `pin: true`. The report renders in the Control UI dashboard and in the iOS app.

## TRMNL

No Jarvis integration. Your TRMNL already runs from TRMNL's own website plugins, so adding a push job would just duplicate it.

## Verify

- [ ] `/controlui` in the Telegram DM opens the Control UI
- [ ] Editing a line in MEMORY.md through the UI is visible to Jarvis in the next turn
- [ ] The *Today* board shows the commitment you added in guide 03
