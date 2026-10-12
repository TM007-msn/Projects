# Setting up the planner on an old Linux laptop

The laptop becomes a small home server. It stays plugged in with the lid shut, running the planner all the
time. You then use the planner from your phone and other computers through a browser or the Claude app.

You'll need roughly an hour the first time. Each step ends with a **Check**. Don't move on until it passes.

Commands are for Ubuntu/Debian-based Linux. Type them in a terminal on the laptop. Anything in `<angle brackets>`
is something you replace.

---

## 1. Stop the laptop going to sleep

A sleeping laptop sends no reminders and Claude can't reach it.

```bash
# Ignore the lid being closed (on battery, on mains, and when docked)
sudo mkdir -p /etc/systemd/logind.conf.d
printf '[Login]\nHandleLidSwitch=ignore\nHandleLidSwitchExternalPower=ignore\nHandleLidSwitchDocked=ignore\n' \
  | sudo tee /etc/systemd/logind.conf.d/no-lid-sleep.conf

# Switch off suspend and hibernate completely
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target

sudo reboot
```

Also:
- Keep it plugged in. If the laptop's settings or BIOS have a **battery charge limit** (often 60–80 %),
  turn it on. Sitting at 100 % all year wears the battery out.
- Optional: in the BIOS, turn on **"Power on after AC loss"** (sometimes called "Restore on AC power") so it
  starts itself after a power cut.

**Check:** close the lid, wait a minute, open it. The terminal should still be there with no login screen.
`systemctl status sleep.target` should say `masked`.

## 2. Install Docker

Docker runs the planner in a sealed box with everything it needs, and restarts it automatically.

```bash
sudo apt update && sudo apt install -y git curl
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER      # lets you run docker without sudo
sudo systemctl enable --now docker # start Docker now and on every boot
```

Log out and back in (or reboot) so the `docker` group change applies.

**Check:** `docker run --rm hello-world` prints "Hello from Docker!", and `docker compose version` prints a version.

## 3. Get the code

```bash
cd ~
git clone https://github.com/TM007-msn/Projects.git
cd Projects/life-planner
git checkout claude/student-life-planner-concept-swr0vw   # until it's merged into main
```

If the repo is private, `git clone` will ask you to log in. Use your GitHub username and a
**personal access token** as the password (GitHub → Settings → Developer settings → Personal access tokens),
or install the GitHub CLI and run `gh auth login` first.

**Check:** `ls` shows `app`, `web`, `docker-compose.yml` and this file.

## 4. Fill in your settings

```bash
cp .env.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # run twice: one token, one ntfy topic
nano .env
```

Fill in:
- `PLANNER_TOKEN` = the first random string. This is effectively your password, so save it in your password manager.
- `NTFY_TOPIC` = the second random string, e.g. `planner-k3J9...`. Anyone who knows it can read your
  notifications, which is why it's random.
- Leave `PUBLIC_HOSTS` empty for now (step 6).

Save in nano with `Ctrl+O`, `Enter`, then quit with `Ctrl+X`.

**Check:** `grep -E '^(PLANNER_TOKEN|NTFY_TOPIC)=.+' .env` prints both lines with values, and `git status`
does **not** list `.env`.
It's ignored on purpose, so your secrets never get committed.

## 5. Start it and try it on home Wi-Fi

```bash
docker compose up -d --build
```

The first build takes a few minutes. After that it restarts by itself after crashes and reboots.

**Check:**
- `curl localhost:8000/api/health` prints `{"ok":true}`.
- `hostname -I` shows the laptop's IP address (the first one, e.g. `192.168.1.42`).
- On your phone, connected to the **same Wi-Fi**, open `http://<that IP>:8000`. Enter your token when asked,
  add a test task, then use **Share → Add to Home Screen** (iPhone) or **⋮ → Install app** (Android).

**Notifications:** install the **ntfy** app on your phone, tap **+**, and subscribe to your `NTFY_TOPIC`.
Test it from the laptop:

```bash
curl -d "Hello from the planner" ntfy.sh/<your NTFY_TOPIC>
```

The notification should appear on your phone within a few seconds.

If the page won't load from your phone but `curl` works on the laptop, check the laptop's firewall:
`sudo ufw status`. If it's active, run `sudo ufw allow 8000/tcp`.

## 6. Reach it from anywhere

You need a public HTTPS address for the dashboard away from home and for the Claude app. There are two routes,
and neither needs port forwarding:

- **Your own domain + a login wall (recommended):** about £8–10 a year for the domain; everything else is free.
  The planner lives at `planner.yourdomain`, behind a Cloudflare login only you can pass, and the laptop can host
  your own websites too. **Follow [`../homelab/GUIDE.md`](../homelab/GUIDE.md) and skip the rest of this step.**
- **No domain yet: Tailscale Funnel.** Free and quick. You get an address like
  `https://<laptop>.<tailnet>.ts.net` protected only by your token. Steps below.

### Tailscale Funnel

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up                 # opens a login link: sign in (free personal account)
sudo tailscale funnel --bg 8000   # publish the planner on your HTTPS address
```

The first time, the funnel command may print a link asking you to enable **HTTPS certificates** and
**Funnel** for your account. Open it, approve it, and run the command again. Tailscale's commands change
now and then, so if one errors, `tailscale funnel --help` shows the current form.

Find your address:

```bash
tailscale funnel status
```

Put that hostname (without `https://`, e.g. `old-laptop.tail1234.ts.net`) in `.env`:

```
PUBLIC_HOSTS=old-laptop.tail1234.ts.net
```

Then restart the planner so it picks up the change: `docker compose up -d`.

**Check:** on your phone, with **Wi-Fi off** (on mobile data), open `https://<your hostname>`. The dashboard
should load and ask for your token. Funnel keeps running in the background and comes back after reboots.

> The planner refuses to start if `PUBLIC_HOSTS` is set without a `PLANNER_TOKEN`, so you can't accidentally
> publish your data with no password. If it won't start, `docker compose logs planner` says why.

## 7. Connect Claude

In the Claude app, add a **custom connector** with the URL:

```
https://<your hostname>/mcp?token=<your PLANNER_TOKEN>
```

`<your hostname>` is `planner.yourdomain` (homelab route) or your `*.ts.net` name (Funnel route).

Then try: *"What's on my plate this week?"* or *"Add my stats problem sheet, due Wednesday 9am"*.

**Caveat:** I'm not certain Claude's custom connectors accept a token in the URL like this. They may
require OAuth sign-in instead. If the connector won't connect, that's the next thing to build (the MCP
library supports OAuth). On the laptop itself, Claude Desktop / Claude Code can always connect to
`http://localhost:8000/mcp`.

## 8. Nightly backups

Your whole planner is one file (`data/planner.db`). Back it up every night at 03:00:

```bash
crontab -e
```

Add this line at the bottom (replace `<you>` with your Linux username; `whoami` tells you):

```
0 3 * * * /home/<you>/Projects/life-planner/scripts/backup.sh >> /home/<you>/planner-backup.log 2>&1
```

**Check:** run `./scripts/backup.sh` once by hand. It should print `backed up to backups/planner-<date>.db`.

Backups on the same laptop won't survive the laptop dying. Every so often, copy the `backups` folder
somewhere else (USB stick, or sync it to Google Drive with `rclone`).

## Looking after it

If you moved to the homelab setup, run these in `~/Projects/homelab` instead (see its GUIDE.md); backups
still run from `life-planner/scripts/backup.sh`.

| Task | Command (run in `~/Projects/life-planner`) |
|---|---|
| Update to the latest code | `git pull && docker compose up -d --build` |
| See what it's doing | `docker compose logs -f planner` (Ctrl+C to stop watching) |
| Restart it | `docker compose restart planner` |
| Stop it | `docker compose down` (your data stays in `data/`) |
| Is it up? | `curl localhost:8000/api/health` |
| Restore a backup | `docker compose down`, `cp backups/planner-<date>.db data/planner.db`, `docker compose up -d` |

After a power cut, Docker, the planner and Tailscale all start by themselves. If you turned on "Power on after
AC loss", you don't need to do anything.

## Security, in short

- With Funnel the address is **public on the internet**. The dashboard page itself is visible to anyone who
  finds the URL, but it holds no data; every task and reminder needs your `PLANNER_TOKEN`. The homelab route
  adds a Cloudflare login wall in front as well.
- Keep the token long and secret. If it leaks, put a new one in `.env`, run `docker compose up -d`, and update
  the Claude connector URL.
- Install security updates on the laptop: `sudo apt update && sudo apt upgrade` every week or two, or turn on
  `unattended-upgrades`.
