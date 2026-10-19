# 09 · Security and reliability

**What:** keep a box that holds your timetable, routines, email and memory safe, and make sure it keeps running without you being a full-time admin.
**Why:** your spec weights reliability at about 80% vs 20% for raw power, and security has to be good enough for personal data. OpenClaw has had serious vulnerabilities, so you need to stay current and keep it off the internet.

## Security checklist

| Control | How | Where |
|---|---|---|
| **Not on the internet** | `gateway.bind: "loopback"`, Tailscale **Serve** only (never Funnel) | Config; guide 00 |
| **One owner** | Telegram `dmPolicy: "allowlist"`, `allowFrom` = your ID only, `commands.ownerAllowFrom` | Config |
| **Least privilege** | Separate `researcher` agent: web only, no skills, no exec, no messaging | Config; guide 07 |
| **Approval gates** | Exec approvals (Telegram buttons / iOS cards) + the autonomy table in `AGENTS.md` | Config + AGENTS.md |
| **Voice can't approve** | Written into `AGENTS.md`; `/say` is loopback-only | Guide 11 |
| **Secrets** | `~/.openclaw/.env`, `chmod 600`, separate gateway and hooks tokens, rotate on suspicion | Guide 00 |
| **Stay current** | Weekly "Update & security check" automation (Mon 09:00) runs `openclaw update status` + `openclaw security audit` | `setup-automations.sh` |
| **Audit community skills** | Read every file before installing; prefer your own or bundled skills; `openclaw skills check` | Below |
| **Memory is reviewable** | Plain Markdown, git history, Sunday review, `openclaw memory forget` | Guide 06 |
| **Private stays local** | No bulk behavioural analysis on cloud models until the local box exists | AGENTS.md; guide 06 |
| **Physical mute** | The mic's mute (or an inline USB switch) beats any software | Guide 11 |

### Installing community skills (ClawHub) safely

```bash
openclaw skills install @owner/some-skill --dry-run 2>/dev/null || true   # where supported
# Better: clone or download it first, read SKILL.md and every script, then:
openclaw skills install ./path/to/reviewed-skill --as some-skill
openclaw skills check
```

Red flags: `curl … | sh`, obfuscated code, network calls to unknown hosts, anything that reads `~/.openclaw` or `.env`.

## Reliability checklist

| Need | How |
|---|---|
| Starts on boot, restarts on crash | systemd user units (`openclaw-gateway`, `jarvis-voice`) + `loginctl enable-linger` |
| Survives updates | `openclaw backup create --verify` before every `openclaw update`; `openclaw doctor --fix` after |
| Knows when it's broken | "Server health" automation every 30 min (disk, memory, services, Gateway, ledger); automation failure alerts after 2 consecutive failures |
| Missed jobs after downtime | `cron.skipMissedJobs: true`, so no stale pile-up of reminders |
| No SSH firefighting | Health alerts say what's wrong; the `server-health` skill can restart the voice daemon itself |

## Backups

1. **Offsite target:** configure one once (see `openclaw backup --help` and the OpenClaw Backups docs for supported targets; an external drive or a cloud bucket both work).
2. **Nightly:** the "Nightly backup" automation (02:30) runs `automations/nightly-backup.sh`. That's `openclaw backup create --to offsite --verify` with 7 daily, 4 weekly and 6 monthly copies, plus a git push of the workspace.
3. **Workspace git repo (private):**
   ```bash
   cd ~/.openclaw/workspace
   printf '.DS_Store\n.env\n**/*.key\n**/*.pem\n**/secrets*\nstate/*.lock\n' > .gitignore
   git init && git add -A && git commit -m "Jarvis workspace"
   gh repo create jarvis-workspace --private --source . --remote origin --push
   ```
4. **Test a restore once** (your spec requires this). Do it on day one, not after you need it:
   ```bash
   openclaw backup list --from offsite
   openclaw backup verify --from offsite latest
   openclaw backup restore --from offsite latest --target ~/restore-test
   ls ~/restore-test && rm -rf ~/restore-test
   ```

## Verify

- [ ] `openclaw security audit --deep` is clean
- [ ] Restore test done (write the date in MEMORY.md → Decisions)
- [ ] `sudo reboot` → Jarvis answers on Telegram within 2 minutes, unattended
- [ ] Stop the voice daemon → a health alert arrives within 30 minutes
