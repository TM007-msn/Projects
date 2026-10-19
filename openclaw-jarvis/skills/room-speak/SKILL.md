---
name: room-speak
description: Say something out loud in Taylor's room through the OptiPlex speaker (voice daemon), falling back to Telegram when Taylor is away.
metadata: { "openclaw": { "emoji": "🔊", "requires": { "bins": ["curl", "python3"] } } }
---

# Room speak

Use this for **interrupt now** items, greetings and check-ins when Taylor is
home. Replies to Taylor's own voice questions are spoken automatically; you
don't need this skill for those.

1. Check presence: `python3 skills/presence/scripts/presence.py get`.
   If the state isn't `home`, send the text on Telegram instead and stop.
2. Speak:
   ```bash
   curl -sS -m 10 -X POST http://127.0.0.1:8765/say \
     -H 'Content-Type: application/json' \
     -d '{"text": "Heads up: your college timetable changed tomorrow. First lesson is now 10:00."}'
   ```
   - `200` with `{"ok": true}` means it was spoken (or queued behind the
     current reply).
   - `423` means the mic is muted or quiet hours are on (23:30–07:00). Send
     it on Telegram instead.
   - Connection refused means the voice daemon is down. Send it on
     Telegram, and mention that the voice daemon isn't running.

## Writing for speech

- One or two short sentences. No URLs, tables, emoji or markdown.
- Say numbers and times naturally: "twenty past eight", "about fifteen
  pounds".
- Don't speak sensitive content (health, money, private messages) aloud.
  Send those on Telegram.
