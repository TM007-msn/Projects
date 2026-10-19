# 02 · Messaging: Telegram + the OpenClaw iPhone app

**What:** how Jarvis reaches you when you're not in your room, and how you reach it.
**Recommendation:** **Telegram** for chat, plus the **official OpenClaw iOS app** for push notifications, approvals and voice. **No iMessage for now.**

## Why this combination

| Option | Verdict | Reason |
|---|---|---|
| **Telegram** | ✅ Primary chat | Already working ("Ace"), official bot API (no ban risk), runs on the Linux OptiPlex, inline buttons (Done / Snooze / Cancel), voice notes, approvals, a pinned chat, and the `/controlui` Mini App dashboard |
| **OpenClaw iOS app** | ✅ Add now | On the App Store. Push notifications, approval cards, answers to Jarvis's questions, **Talk voice** (Jarvis by voice from anywhere), a Siri / Action-button "Start Live Voice" shortcut, Apple Watch. This replaces the spec's Phase 4 "build my own app" |
| iMessage | ❌ Skip | OpenClaw now supports it only through `imsg` on a **signed-in Mac** (BlueBubbles was removed). Full features need SIP disabled, it needs a second Apple ID, and Apple updates break it. Revisit only if you buy the Mac Studio |
| WhatsApp | ❌ | Unofficial bridge; the number can get banned |
| Signal | Possible, not worth it | Works, but it's no better than Telegram for this, and its setup is fiddlier |
| Discord | ❌ | Feels like a server, not "texting a person" |

## Telegram setup and hardening

1. Bot: you already have one. If you're re-creating it, use @BotFather → `/newbot`, then `/setprivacy` → Enable.
2. Get your numeric user ID from @userinfobot.
3. Config (from `config/openclaw.json5.example`):
   - `channels.telegram.dmPolicy: "allowlist"` with `allowFrom: ["<your id>"]`, so **only you** can talk to it.
   - `commands.ownerAllowFrom: ["telegram:<your id>"]`, which makes you the owner (needed for automation management, approvals and standing intents).
   - `capabilities.inlineButtons: "dm"` and `execApprovals.enabled: "auto"`.
4. In Telegram: **pin** the Jarvis chat, and set notifications to normal (not muted). The interruption tiers already keep it quiet.
5. Voice notes: hold the mic in Telegram and talk. `tools.media.audio` transcribes them, so you can talk to Jarvis on the bus.
6. Mini App dashboard: send `/controlui` in the DM (needs `gateway.tailscale.mode: "serve"` and Tailscale on your phone).

Optional later: a private Telegram **group with forum topics** (Main / Jobs / Alerts) to separate job results and alerts from conversation. Not needed for Phase 1.

## iPhone app setup

1. Install **OpenClaw** from the App Store, and Tailscale on the phone.
2. Pair it with the Gateway (see `openclaw qr` or the app's pairing screen; it connects over the tailnet).
3. Allow notifications. Push uses OpenClaw's hosted relay for App Store builds, so the Gateway doesn't need an APNs key.
4. Shortcuts → OpenClaw → **Start Live Voice** → assign it to the Action button. That gives you "talk to Jarvis" anywhere.
5. Approvals: when Jarvis asks permission (e.g. to create a calendar event), the card appears in the app as well as in Telegram.

## The "arrive home" / "leave home" shortcuts (presence)

These tell Jarvis whether to speak in your room or message your phone. They also trigger the evening check-in.

iPhone **Shortcuts → Automation → New → Arrive** (home location) → *Run immediately*:
- Action **Get Contents of URL**
  - URL: `https://<optiplex>.<tailnet>.ts.net/hooks/wake`. Tailscale Serve exposes the Gateway's HTTP port. Alternatively use `http://<optiplex-tailscale-ip>:18789/hooks/wake` if you expose it on the tailnet interface.
  - Method: POST. Headers: `Authorization: Bearer <OPENCLAW_HOOKS_TOKEN>`, `Content-Type: application/json`
  - Body (JSON): `{"text": "PRESENCE: home (iOS arrive). Set presence, then if it's after 15:00 start the evening check-in.", "mode": "now"}`

Make a matching **Leave** automation with `{"text": "PRESENCE: away (iOS leave). Set presence; no reply needed.", "mode": "now"}`.

Tailscale must be connected on the phone for these to work. Turn on its "always on" VPN setting.

## Verify

- [ ] A message from another Telegram account gets no reply
- [ ] A voice note → Jarvis answers the transcribed question
- [ ] iOS app: Start Live Voice → ask "what's my next commitment?"
- [ ] Walk out and back in → `python3 skills/presence/scripts/presence.py get` flips away → home
