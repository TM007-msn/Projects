# 03 · The accountability loop

**What:** Jarvis records what you say you'll do, checks in, and gets firmer if you put it off.
**Why:** your spec calls this *the* defining feature: "where most of the productivity gain comes from". It needs no new hardware. **Build this first.**

## How it fits together

```
You: "I'll do the maths past paper by 8"
        │  (commitments skill)
        ▼
state/commitments.json  ◄── commitments.py (the only thing that edits it)
        ▲                                   │
        │ records each nudge                │ `due` (read-only)
        │                                   ▼
commitment-checkin skill ◄── fires ── Commitment watcher automation
 (voice if home, Telegram always)       every 5 min, trigger script, no model call on quiet ticks
```

## The rules (enforced by code, not by the model remembering them)

| Rule | Where it's enforced |
|---|---|
| A commitment has a **time** | `add --due` is required; a due time in the past is rejected |
| Your own words are quoted back | `add --quote` (the skill always passes it) |
| **Snooze needs a new time** and is logged | `snooze --to` is required and must be in the future; it's added to the snooze history |
| **Cancel needs a reason**, raised in the evening review | `cancel --reason` is required and can't be blank |
| Ladder: friendly (−30 min) → reminder quoting you (at due) → **firm** (+30 min) → **stop** | `due` never returns anything after stage 3 |
| If Jarvis was offline, you get **one** message, not three | `due` returns only the highest overdue stage |
| "Stop nagging" counts as a snooze | `AGENTS.md` + `commitments` skill |
| Physical mute always wins | Hardware; Jarvis never argues |

The ladder's fourth step in your spec, "switch channel to the phone", is a **delivery rule**: whichever stage fires while presence is `away` goes to Telegram instead of the speaker.

## Setup

1. The skills are already in the workspace (guide 00): `commitments`, `commitment-checkin`, `presence`, `room-speak`.
2. Run the tests once on the OptiPlex: `cd ~/openclaw-jarvis && python3 -m pytest tests/`.
3. Create the automations: `TELEGRAM_CHAT_ID=<id> bash automations/setup-automations.sh`. This creates the **Commitment watcher** (`--every 5m` + `automations/commitment-watcher.js`).
4. Set up the iOS arrive/leave shortcuts (guide 02), so presence is right.

## Try it (10 minutes, on Telegram)

1. "I'll tidy my desk by HH:MM" with a time 35 minutes away.
2. Jarvis confirms: "Locked in: tidy desk by HH:MM."
3. About 5 minutes later the friendly check-in arrives (stage 1, 30 minutes before).
4. Reply "snooze to <time +20>". It should accept. Then try "snooze" with no time, and it should ask for one.
5. Reply "cancel" and it should ask for a reason.
6. Check the ledger: `python3 ~/.openclaw/workspace/skills/commitments/scripts/commitments.py list --all`.

## Tuning (the "nag tuning" risk in your spec)

- Ladder offsets live in `LADDER` at the top of `commitments.py` (−30 / 0 / +30 minutes). If the friendly check-in feels too early, change it to −15.
- If the firm message feels harsh, edit the stage 3 example in `skills/commitment-checkin/SKILL.md`. Don't add more stages.
- Watch the **weekly review** completion rate for 2 weeks before changing anything. Judge by whether more gets done, not by whether it feels nice.

## Verify

- [ ] All 10 commitment tests pass
- [ ] Stage 1 → 2 → 3 arrive at the right times for a test commitment, then nothing more
- [ ] Snooze without a time is refused; cancel without a reason is refused
- [ ] With presence `home`, stage 2 is spoken in the room **and** appears on Telegram
- [ ] The end-of-day summary lists done / snoozed / cancelled (with the reason)
