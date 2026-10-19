---
name: commitment-checkin
description: Send the due escalation-ladder nudge for a commitment (friendly, reminder, firm) on the right channel. Used by the commitment watcher automation.
metadata: { "openclaw": { "emoji": "⏰", "requires": { "bins": ["python3"] } } }
---

# Commitment check-in (escalation ladder)

The commitment watcher automation runs this when a ladder stage falls due.
Its message contains the JSON from `commitments.py due`. Each item has `id`,
`what`, `quote`, `due`, `stage` (1–3), `stage_name`, `snooze_count` and
`minutes_past_due`.

## For each item

1. **Pick the channel.** Run `python3 skills/presence/scripts/presence.py get`.
   - `home`: speak it with the `room-speak` skill, **and** send it on Telegram
     with the message tool, so there's a record and buttons.
   - `away` or `unknown`: send it on Telegram with the message tool only.
     This is ladder step 4, "switch channel to the phone".
   - The Telegram target is the owner DM (the chat ID in the automation text,
     or `commands.ownerAllowFrom`).
2. **Write the message for the stage.** Keep it to one or two sentences, use
   British English, and don't use emoji spam.

| Stage | Tone | Example |
|---|---|---|
| 1 friendly | Light check-in, about 30 min before due | "How's the past paper going? 30 minutes to your 20:00 target." |
| 2 reminder | Quote Taylor's own words | "You said: 'I'll have it done by 8.' It's 20:00. Done, or do you need a new time?" |
| 3 firm | Direct, ask for a decision | "It's 20:30 and the past paper isn't marked done. What's the new time, or are you cancelling it (with a reason)?" |

   If `snooze_count` ≥ 2, you may mention it once, factually ("That's the third
   time this has moved tonight"). Don't guilt-trip.
3. **Offer the next actions.** On Telegram, add inline buttons if available:
   **Done**, **Snooze 30m**, **New time…**, **Cancel…**. Otherwise end with
   "Reply done / snooze HH:MM / cancel + reason."
4. **Record it.** After the message is sent successfully:
   `python3 skills/commitments/scripts/commitments.py nudged <id> --stage <stage> --channel <voice|telegram>`.
   If sending failed, do **not** record it, so the watcher retries.
5. When every item is handled, reply `NO_REPLY` (the messages have already gone).

## Rules

- The ladder stops at firm. Never invent a stage 4 nag, and never repeat a
  stage that's already recorded.
- Between 23:30 and 07:00, don't speak aloud. Send Telegram only, and only for
  stage 3.
- If Taylor replies, handle it with the `commitments` skill (done / snooze / cancel).
