# openclaw-jarvis

Plan, guides, skills and automations for **Jarvis**: a proactive personal assistant and accountability partner on OpenClaw 2026.10.5, running on a Dell OptiPlex with Telegram, the OpenClaw iPhone app and a room speaker.

**Start with [`PLAN.md`](PLAN.md).**

## What's here

| Path | What |
|---|---|
| `PLAN.md` | Vision, decisions, architecture, roadmap with gates, must-have checklist, costs, risks |
| `guides/` | One guide per area (what, why, how, verify), in build order: `00-foundations` … `13-files-notes-pc` |
| `workspace/` | Templates for `~/.openclaw/workspace`: AGENTS.md (standing orders), SOUL.md, IDENTITY.md, USER.md, MEMORY.md, tasks.md |
| `skills/` | 12 Jarvis skills (`SKILL.md` + scripts): commitments, commitment-checkin, morning-briefing, evening-checkin, end-of-day-summary, weekly-review, revision-planner, research-job, memory-review, server-health, room-speak, presence |
| `automations/` | `setup-automations.sh` (all 10 jobs, idempotent), the commitment watcher trigger script, the backup script, and a schedule table |
| `config/openclaw.json5.example` | Config blocks to merge into `~/.openclaw/openclaw.json` (validated with `openclaw config validate`) |
| `voice/` | Room-voice daemon for the OptiPlex (wake word → Whisper → Jarvis → Piper), systemd unit, config, tests |
| `tests/` | Tests for the commitments ledger |

## Install order (on the OptiPlex)

```bash
git clone https://github.com/TM007-msn/Projects.git ~/projects-repo
ln -s ~/projects-repo/openclaw-jarvis ~/openclaw-jarvis
cd ~/openclaw-jarvis
```

1. `guides/00-foundations.md`: upgrade, service, Tailscale, workspace files and skills
2. `guides/02-messaging.md`: Telegram hardening, iOS app, presence shortcuts
3. `guides/03-accountability-loop.md` + `04-daily-rhythm.md`: `bash automations/setup-automations.sh`
4. Then 05 → 07, 09 (backups and the restore test), and 11 (voice) once you have a speaker

## Tests

```bash
python3 -m pip install pytest httpx
python3 -m pytest tests voice/tests        # 28 tests
```

## What was verified, and what wasn't

Verified on 19/10/2026 in a sandbox with a real OpenClaw 2026.10.5 Gateway:
- config validates
- all 12 skills load (`revision-planner` correctly waits for `gog` to be installed)
- all 10 automations are created with the right schedules, and re-running the script makes no duplicates
- the watcher trigger fires on a due commitment and stays quiet otherwise
- the voice daemon's Gateway client works against the real `/v1/chat/completions` (main session, voice channel), including its fallback when the model is unavailable
- the openWakeWord "hey jarvis" model loads and runs about 5 ms per frame with no false wakes on silence or noise

**Not verified** (can't be done from a cloud sandbox; these are the first on-device checks):
- a real model reply (the sandbox had no API key)
- Telegram delivery
- Whisper and Piper (model downloads were blocked by the sandbox proxy)
- the XVF3800 microphone and speaker
- end-to-end voice latency
