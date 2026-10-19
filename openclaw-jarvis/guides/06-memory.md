# 06 · Memory you can see, edit and delete

**What:** Jarvis remembers useful things indefinitely, with every memory visible, tagged and editable.
**Why:** "memory control is critical" (your spec). OpenClaw stores memory as **plain Markdown in the workspace**: there's no hidden state.

## Where things go

| Layer | File | Example |
|---|---|---|
| Preferences (directives) | `USER.md` | "Always use DD/MM/YYYY dates." |
| Durable facts and decisions | `MEMORY.md` | "Econ mock on 12/01/2027. [stated]" |
| Daily log | `memory/YYYY-MM-DD.md` | Debriefs, what happened, jobs finished |
| Dream diary | `DREAMS.md` | OpenClaw's background consolidation notes |
| Temporary | The conversation itself | Not saved |

Your spec's three levels map like this: **explicit** = `[stated]`, **inferred** = `[inferred]`, **temporary** = conversation only.

## The stated / inferred rule

Every line in `MEMORY.md` ends with `[stated]` (you said it) or `[inferred]` (Jarvis worked it out). This is written into `AGENTS.md`. The Sunday **memory review** lists new `[inferred]` lines and you reply "keep 1, delete 2, fix 3: …":
- keep → the tag becomes `[stated]`
- fix → rewritten and tagged `[stated]`
- delete → removed

## Dreaming (on by default)

OpenClaw's **dreaming** sweep consolidates daily notes into `MEMORY.md` in the background, and writes a diary to `DREAMS.md`. Two things to know:

1. Dreaming may add lines without tags. The memory review treats untagged new lines as `[inferred]`.
2. Dreaming uses your cloud model. That's fine for facts you've already told Jarvis. When the local box arrives, point it at a local model (`plugins.entries.memory-core.config.dreaming.model`).

## Seeing and editing memory

- **Files:** `~/.openclaw/workspace/MEMORY.md` etc. Edit them in any editor.
- **Control UI:** Settings → Agents → Files (also via `/controlui` in Telegram).
- **Chat:** "What do you remember about my exams?", "Forget that I said X", "Show me everything you've inferred".
- **History:** the workspace is a private git repo (guide 09), so `git log -p MEMORY.md` shows every change and you can undo any of them.
- **Hard delete** of memory derived from a session: `openclaw memory forget --dry-run …`, then without `--dry-run` (see the OpenClaw memory provenance docs).

## Behavioural learning: the privacy line

Your spec says behavioural pattern analysis must run **on a local model only**. With the OptiPlex only, there's no capable local model yet, so the plan:

- **Now:** Jarvis may note simple patterns it sees in normal conversation ("snoozes cluster after 21:00"), tagged `[inferred]`, for you to review. **No** bulk "analyse my behaviour" jobs on cloud models (this is in `AGENTS.md`).
- **After the local box (guide 12):** a weekly pattern-analysis job pinned to the local model, plus dreaming on the local model.

## Verify

- [ ] "Remember my Econ mock is 12/01/2027" → a `[stated]` line in MEMORY.md
- [ ] Sunday memory review arrives and lists `[inferred]` items
- [ ] "Delete 1" → the line is gone, and `git log -p MEMORY.md` shows the removal
