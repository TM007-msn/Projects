---
name: server-health
description: Check the OptiPlex (disk, memory, Gateway, voice daemon, commitments file) and explain or fix problems. Use for "is everything OK?" or a health alert.
metadata: { "openclaw": { "emoji": "🩺", "os": ["linux"], "requires": { "bins": ["bash", "python3"] } } }
---

# Server health

Run: `bash {baseDir}/scripts/health.sh`

- Prints `NO_REPLY` when everything is fine. Tell Taylor "All healthy" in
  one line.
- Otherwise prints one line per problem. For each one, explain what it
  means in plain English and what to do about it.

## Safe fixes (automatic)

- Restart a stopped voice daemon: `systemctl --user restart jarvis-voice`.
- Clear old logs or caches inside `~/.openclaw` with `openclaw doctor`'s
  suggestions.

## Needs approval

- Anything with `sudo`, deleting files outside caches, restarting the
  Gateway itself, or package upgrades. Ask first, and say exactly what
  the command will do.

If the same problem shows up three checks in a row, raise it as **interrupt
now** with the likely cause.
