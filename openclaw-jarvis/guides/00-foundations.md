# 00 · Foundations: a solid OptiPlex base

**What:** bring the existing "Ace" OpenClaw install on the OptiPlex up to date, make it start on its own and recover from crashes, lock it to your tailnet, and turn it into Jarvis.
**Why:** reliability is priority 2 of 12, right behind proactivity. Everything else assumes the Gateway is always up and not exposed to the internet.
**Time:** about 1.5 hours.

## 1. Back up before you touch anything

```bash
openclaw backup create --verify          # local archive of config, state DBs and workspace
ls ~/.openclaw/backups 2>/dev/null || openclaw backup list
```

## 2. Upgrade OpenClaw to the current release

You need **v2026.10.5 or later**. Your spec's floor of v2026.1.29 (the RCE fix) is long out of date. OpenClaw needs Node 24.16+.

```bash
node --version                     # must be v24.16+ (or 26.1+)
openclaw update status             # what you're on and what's available
openclaw update                    # upgrade + restart
openclaw doctor --fix              # migrate old config/state (heartbeat tasks, cron store, etc.)
openclaw --version
```

If Node is too old: `curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash - && sudo apt install -y nodejs`, then rerun the update.

> Things that changed since your spec: `openclaw cron` is now an alias of `openclaw automations`. Heartbeat tasks moved out of `HEARTBEAT.md` into automations (doctor converts them). BlueBubbles was removed.

## 3. Run it as a service that survives reboots and crashes

```bash
openclaw gateway install               # writes the systemd user unit (openclaw-gateway.service)
systemctl --user enable --now openclaw-gateway.service
loginctl enable-linger "$USER"          # keep it running with nobody logged in
systemctl --user status openclaw-gateway.service
```

The unit restarts on failure. To check it, `kill -9` the Gateway process and watch it come back within a few seconds:

```bash
journalctl --user -u openclaw-gateway.service -f
```

## 4. Network: tailnet only, never the public internet

1. Install Tailscale on the OptiPlex and your iPhone (`curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up`).
2. In `~/.openclaw/openclaw.json`, keep `gateway.bind: "loopback"` and set `gateway.tailscale.mode: "serve"`. See `config/openclaw.json5.example`.
3. Make sure nothing listens publicly:
   ```bash
   ss -tlnp | grep 18789        # should show 127.0.0.1 only
   openclaw security audit --deep
   ```
4. **Never** use Tailscale **Funnel** for the Gateway. Funnel makes it public.

## 5. Secrets

```bash
nano ~/.openclaw/.env           # TELEGRAM_BOT_TOKEN=..., OPENCLAW_GATEWAY_TOKEN=..., OPENCLAW_HOOKS_TOKEN=..., ANTHROPIC_API_KEY=...
chmod 600 ~/.openclaw/.env
```

- Generate tokens with `openssl rand -hex 32`. Use a different one for the gateway and for hooks.
- Rotate any token you have ever pasted into a chat, a screenshot or a repo.

## 6. Rename Ace → Jarvis and install the workspace files

```bash
git clone https://github.com/TM007-msn/Projects.git ~/projects-repo
ln -s ~/projects-repo/openclaw-jarvis ~/openclaw-jarvis     # the voice service expects this path

cd ~/.openclaw/workspace
cp ~/openclaw-jarvis/workspace/{AGENTS.md,SOUL.md,IDENTITY.md} .
# USER.md / MEMORY.md: merge by hand if Ace already has content; otherwise copy.
cp -n ~/openclaw-jarvis/workspace/{USER.md,MEMORY.md,tasks.md} .
mkdir -p research state && cp -n ~/openclaw-jarvis/workspace/research/JOBS.md research/
mkdir -p skills && cp -r ~/openclaw-jarvis/skills/* skills/
openclaw skills list            # the 12 Jarvis skills should appear
openclaw skills check
```

Then merge the relevant blocks of `config/openclaw.json5.example` into `~/.openclaw/openclaw.json`, and run `openclaw config validate && openclaw gateway restart`. Start a fresh chat with `/new` so the new persona loads.

## 7. Models and cost

| Use | Model | Why |
|---|---|---|
| Everyday chat, briefings, check-ins | Sonnet (`anthropic/claude-sonnet-5-5`) | Fast, good tool use, sensible cost |
| Deep research, planning | Opus (`/model opus`, or `--model opus` on a job) | Only when it's worth it |
| Fallback | GPT (`openai/gpt-5.4`) | Keeps Jarvis working during an Anthropic outage |

Budget: **£10–30/month**. Keep the heartbeat off (the automations replace it), let the watcher's trigger script skip quiet ticks for free, and check spend weekly with `/usage cost`. If a month runs hot, the first thing to cut is research-job depth.

## Verify

- [ ] `openclaw --version` shows ≥ 2026.10.5, and `openclaw doctor` is clean
- [ ] The Gateway comes back on its own after `sudo reboot`
- [ ] `ss -tlnp` shows nothing on 0.0.0.0 for OpenClaw
- [ ] `openclaw security audit` shows no critical findings
- [ ] Telegram: "who are you?" → it answers as Jarvis
