---
name: presence
description: Get or set whether Taylor is home or away (set by the iOS arrive/leave shortcuts). Decides voice in the room vs phone message.
metadata: { "openclaw": { "emoji": "🏠", "requires": { "bins": ["python3"] } } }
---

# Presence

```bash
python3 {baseDir}/scripts/presence.py get                         # {"state": "home"|"away"|"unknown", ...}
python3 {baseDir}/scripts/presence.py set home --source ios-arrive
python3 {baseDir}/scripts/presence.py set away --source ios-leave
```

- The iOS Shortcuts automations call the Gateway's `/hooks/wake` with text
  starting `PRESENCE:`. When you see `PRESENCE: home` or `PRESENCE: away`,
  run the matching `set` command first.
- On `PRESENCE: home` in the evening, start the `evening-checkin` skill.
- If Taylor says "I'm home", "back" or "heading out", update presence too.
- Treat `unknown` (no update for 18+ hours) as **away**. Messaging the phone
  is the safe fallback.
