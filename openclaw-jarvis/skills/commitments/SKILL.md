---
name: commitments
description: Record, list, snooze, cancel or complete Taylor's commitments (the accountability loop ledger). Use whenever a plan gets a time attached.
metadata: { "openclaw": { "emoji": "📌", "requires": { "bins": ["python3"] } } }
---

# Commitments ledger

A commitment is one specific thing Taylor said they will do, with a time:
"Maths past paper done by 20:00". The ledger is the single source of truth
for the accountability loop. **Never edit `state/commitments.json` directly.**
Always use the script, because it enforces the rules.

Script: `python3 {baseDir}/scripts/commitments.py` (add `--json` before the
subcommand for machine-readable output).

## When to add one

- Taylor states a plan with a time ("I'll do the past paper by 8").
- The evening check-in turns tonight's priority into a commitment.
- Taylor gives a plan with no time: ask "By when?" before adding. A
  commitment without a time is not a commitment.

```bash
python3 {baseDir}/scripts/commitments.py add \
  --what "Maths past paper (Paper 2, 2023)" \
  --due 20:00 \
  --quote "I'll have it done by 8"
```

Always pass `--quote` with Taylor's own words, as close to verbatim as possible.
Reminders quote them back.

## Changing one

| Taylor says | Command | Rule |
|---|---|---|
| "Done" / "finished it" | `done <id>` | Congratulate briefly; no lecture. |
| "Later" / "give me an hour" | `snooze <id> --to HH:MM --reason "..."` | A snooze **must** have a new time. If none is given, ask for one. |
| "Not doing it" | `cancel <id> --reason "..."` | A cancel **must** have a reason. It is raised in the evening review. |
| "Stop nagging" / "turn off" | treat as a snooze | Ask for the new time. Avoiding a commitment is not an off switch. |

The hard off switch is the physical mic mute and Telegram's own mute.
Jarvis does not argue with those.

## Looking things up

```bash
python3 {baseDir}/scripts/commitments.py list          # open commitments
python3 {baseDir}/scripts/commitments.py list --all    # include closed
python3 {baseDir}/scripts/commitments.py summary       # today's done/snoozed/cancelled/open
```

If the script prints `error: ...` and exits with code 2, a rule was broken.
Explain the rule to Taylor in one sentence and ask for what's missing; don't retry blindly.
