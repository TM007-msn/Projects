# Homelab guide: your own domain, a login wall, and room for experiments

This turns the laptop into a small web host. Your site lives at `yourdomain`, the planner at
`planner.yourdomain`, and anything else you build gets its own subdomain. A Cloudflare login page sits in
front of all of it, so **only you** can get in, and it all works without port forwarding.

```
Browser ─> Cloudflare (DNS, HTTPS, login wall) ─> cloudflared (outgoing tunnel from the laptop)
        ─> Caddy (picks a container by hostname) ─┬─> yourdomain, www  -> sites/home (static files)
                                                  ├─> planner.yourdomain -> planner container
                                                  └─> next.yourdomain    -> your next experiment
```

**Before you start:** do `life-planner/SETUP.md` steps 1–5 (laptop prepared, Docker installed, code cloned,
planner `.env` filled in, working on home Wi-Fi). You don't need its Tailscale Funnel step if you're doing this.

Cloudflare's dashboard gets reorganised every so often. If a menu name below doesn't match exactly, look for
the closest equivalent; the concepts stay the same.

---

## 1. Buy a domain

- **Compare the renewal price, not the first-year price.** Cheap first-year deals (£1 for `.xyz` or `.site`)
  often renew at £10–30 a year. `.co.uk` / `.uk` usually renew cheaply; check the current price.
- The easiest route is to buy it from **Cloudflare Registrar** (Cloudflare dashboard → Domain Registration).
  It sells at cost and skips step 2. Otherwise buy from any UK-friendly registrar (e.g. Porkbun, Namecheap)
  and do step 2.
- Turn on **WHOIS privacy** if the registrar offers it, so your name and address aren't published.

**Check:** the registrar shows the domain as yours and active.

## 2. Move the domain's DNS to Cloudflare (skip if you bought it from Cloudflare)

1. Make a free Cloudflare account, then **Add a domain** and pick the **Free** plan.
2. Cloudflare gives you two nameservers (like `ada.ns.cloudflare.com`). At your registrar, replace the existing
   nameservers with those two.
3. Wait. It's usually under an hour but can take up to a day.

**Check:** the domain shows as **Active** in Cloudflare.

## 3. Create the tunnel

1. Cloudflare dashboard → **Zero Trust** (it may ask you to pick a team name; anything works) →
   **Networks → Tunnels → Create a tunnel** → type **Cloudflared** → name it e.g. `laptop`.
2. On the install screen, choose **Docker**. It shows a command containing `--token eyJ...`. Copy just the
   long token string, without starting the container it suggests; `docker compose` does that for you.
3. Next, add **public hostnames** (sometimes called "published application routes"). Add three, all with
   service type **HTTP** and URL **`caddy:80`**:

   | Subdomain | Domain | Service |
   |---|---|---|
   | *(blank)* | yourdomain | `http://caddy:80` |
   | `www` | yourdomain | `http://caddy:80` |
   | `planner` | yourdomain | `http://caddy:80` |

   Every hostname goes to Caddy, and Caddy decides what to show. That keeps all your routing in one file you
   control (`Caddyfile`).

**Check:** the tunnel is listed. It shows as *inactive* until step 5; that's expected.

## 4. Fill in the settings

```bash
cd ~/Projects/homelab
cp .env.example .env
nano .env        # DOMAIN=yourdomain (no https://), TUNNEL_TOKEN=the token from step 3
```

Then tell the planner its new public name, in `~/Projects/life-planner/.env`:

```
PUBLIC_HOSTS=planner.yourdomain
```

**Check:** `docker compose config -q` (inside `homelab/`) prints nothing. If a setting is missing, it says
which one.

## 5. Switch the planner over and start everything

The planner now runs as part of the homelab, so stop the standalone copy first (otherwise both try to use
port 8000):

```bash
cd ~/Projects/life-planner && docker compose down
cd ~/Projects/homelab && docker compose up -d --build
```

**Check:**
- `docker compose ps` shows `caddy`, `cloudflared` and `planner` all **running**.
- The tunnel shows as **Healthy** in Cloudflare.
- `https://yourdomain` shows the starter page and `https://planner.yourdomain` shows the planner.
  They're **not protected yet**, so do step 6 straight away.

## 6. Put the login wall up (Cloudflare Access)

**Zero Trust → Access → Applications → Add an application → Self-hosted.**

**Application 1, "Everything":**
- Name: `Homelab`. Add three public hostnames: `yourdomain`, `www.yourdomain`, `planner.yourdomain`.
- Session duration: **1 month**, so you aren't logging in every day.
- Policy: name `Only me`, action **Allow**, include **Emails** → your email address.
- Login method: **One-time PIN** (it's on by default). Cloudflare emails you a code when you log in.

**Application 2, "Claude's way in":** the Claude app can't receive an email code, so the planner's `/mcp`
path skips the login wall. It's still protected by your `PLANNER_TOKEN`.
- Name: `Planner MCP`. Hostname `planner.yourdomain` with path **`mcp`**.
- Policy: action **Bypass**, include **Everyone**.

Access applies the most specific match, so `/mcp` uses application 2 and everything else uses application 1.

Zero Trust's free plan covers this (it's free for small numbers of users). It may ask for a payment method
when you first set up Zero Trust. I'm not sure whether it currently does, so check what it shows you before
entering anything.

**Check:**
- In a **private/incognito window**, `https://yourdomain` shows a Cloudflare login page, not your site. Enter
  your email, then the code, and your site appears.
- A different email address gets no code and no access.
- `https://planner.yourdomain/mcp` gives a planner error about the token (401), not the Cloudflare login page.
  That shows the bypass works and the token is still guarding it.

## 7. Connect Claude

Custom connector URL: `https://planner.yourdomain/mcp?token=<your PLANNER_TOKEN>`

The caveat from `life-planner/SETUP.md` step 7 still applies: if Claude's connectors don't accept a token in the
URL, OAuth support is the next thing to build.

## 8. Add another website

Say you want `blog.yourdomain`:

1. Make the folder and a page: `mkdir sites/blog` and put an `index.html` in it.
2. In `Caddyfile`, uncomment the `blog` example block (or copy it and change the name).
3. Reload Caddy: `docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile`
4. In the tunnel (step 3), add the public hostname `blog` → `http://caddy:80`.
5. In Access (step 6), add `blog.yourdomain` to the **Homelab** application, or make a new application with
   no policy if you want this one public.

**Check:** `https://blog.yourdomain` in a private window shows the login page, then your blog.

Editing files in `sites/` shows up immediately. Only `Caddyfile` changes need step 3's reload.

## 9. Add an app (a container)

Static sites are only the start. Anything that ships as a Docker image can be added the same way. To try
**Uptime Kuma** (a dashboard that checks your sites are up and can alert you through ntfy):

1. In `docker-compose.yml`, uncomment the `uptime-kuma` service and the `uptime_kuma:` volume at the bottom.
2. In `Caddyfile`, uncomment the `status` block.
3. `docker compose up -d`, then reload Caddy (step 8.3).
4. Add `status` to the tunnel and to the Access application.

**Check:** `https://status.yourdomain` asks you to create an Uptime Kuma admin account.

The pattern is always the same: **a service in `docker-compose.yml` + a block in `Caddyfile` + a tunnel
hostname + an Access rule.** Other good things to try: Forgejo (your own GitHub), a Python/Flask app you've
written, or Jellyfin (media server).

## 10. Optional: reach the laptop's terminal from anywhere (Tailscale)

Install Tailscale on the laptop and your other computer/phone, then on the laptop:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh
```

Now `ssh <your-username>@<laptop-name>` works from any device on your Tailscale account, even from uni. This is
private: nobody else can see it, and it doesn't need Funnel.

---

## Day to day

| Task | Command (in `~/Projects/homelab`) |
|---|---|
| Start / apply changes | `docker compose up -d` |
| Rebuild after `git pull` | `git pull && docker compose up -d --build` |
| What's running? | `docker compose ps` |
| Logs (one service) | `docker compose logs -f caddy` (or `planner`, `cloudflared`) |
| Reload Caddyfile | `docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile` |
| Stop everything | `docker compose down` (data is kept) |

The planner's nightly backup (`life-planner/scripts/backup.sh`) works unchanged; it finds the planner container
whichever folder started it.

## When things go wrong

- **Site shows a Cloudflare "Bad gateway" / 502:** the container behind it isn't running. Check
  `docker compose ps` and `docker compose logs <service>`.
- **"Not found" from Caddy:** the hostname reached Caddy but there's no block for it in `Caddyfile`, or you
  forgot to reload it.
- **Tunnel "Down" in Cloudflare:** `docker compose logs cloudflared`. Usually a wrong `TUNNEL_TOKEN`.
- **Planner dashboard shows errors after a long time:** your Access session expired. Reload the page and log in.

## Security, in short

- Nothing on the laptop is reachable from the internet except through the tunnel, and the tunnel only reaches
  Caddy. No ports are open on your router.
- Cloudflare Access blocks everyone except your email before requests even reach the laptop. The planner's
  token is a second lock, and the only lock on `/mcp`.
- Keep `.env` files private (they're git-ignored), keep the laptop updated (`sudo apt update && sudo apt
  upgrade`), and use the Access rule for anything with an admin page.
