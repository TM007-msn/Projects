# H446 Revision

A self-hosted, mobile-first revision app for OCR A Level Computer Science (H446): a spec tracker,
keyword summaries with a cover mode, and (in later phases) spaced-repetition flashcards, memory
games and auto-marked tests. Built for one user on a home server, reachable over the LAN and
Tailscale.

> Status: **Phase 2** (spec tracker, login, keyword summaries for every topic). The full README, including
> flashcards, tests, offline use and progress export, is finished at the end of the build.

## Run it

Requires Docker with the Compose plugin.

```bash
git clone <repo> && cd Projects/h446-revision
cp .env.example .env
mkdir -p data                      # must be writable by uid 1000 (your normal Ubuntu user usually is)

# 1. Password hash (prompts twice; paste the output into APP_PASSWORD_HASH in .env)
docker compose build
docker compose run --rm app python -m app.hashpw

# 2. Cookie signing key (paste into SECRET_KEY in .env)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

docker compose up -d
```

Open `http://<server-ip>:8000` on the LAN, or `http://<tailscale-name>:8000` over Tailscale.

If `data/` was created by root, fix it with `sudo chown 1000:1000 data`.

### Environment variables

| Variable | Required | Default | Meaning |
|---|---|---|---|
| `APP_PASSWORD_HASH` | yes | | Output of `python -m app.hashpw` (scrypt; contains no `$`, so it is safe in `.env`). |
| `SECRET_KEY` | yes | | At least 32 random characters. Signs the login cookie; changing it logs out every device. |
| `PORT` | no | `8000` | Port inside and outside the container. |
| `COOKIE_SECURE` | no | `false` | Set `true` only when serving over HTTPS. |
| `SESSION_DAYS` | no | `30` | How long a login lasts. |
| `DATA_DIR` | no | `/data` | Where the SQLite file lives (the compose file mounts `./data`). |
| `CONTENT_DIR` | no | `/app/content` | Content JSON (the compose file mounts `./content` read-only). |

## Back up and restore progress

Progress is one SQLite file, `data/revision.sqlite3`: an append-only log of ratings, flags and
verifications. Content lives in git, so only this file needs backing up.

```bash
# Safe online backup (works while the app is running)
docker compose exec app python -c "import sqlite3; sqlite3.connect('/data/revision.sqlite3').backup(sqlite3.connect('/data/backup.sqlite3'))"
cp data/backup.sqlite3 ~/backups/h446-$(date +%Y%m%d).sqlite3

# Restore
docker compose down
cp ~/backups/h446-YYYYMMDD.sqlite3 data/revision.sqlite3
rm -f data/revision.sqlite3-wal data/revision.sqlite3-shm
docker compose up -d
```

## Content

Everything you revise from is JSON in `content/`, versioned in git. Edits show up after a browser
refresh (no rebuild), because `./content` is mounted into the container.

| File | What it holds |
|---|---|
| `spec.json` | Every spec point (generated, don't hand-edit; see below). |
| `keywords.json` | Keywords: term, acronym, definition, spec ids, related keywords, "don't confuse with". |
| `summaries/<subtopic>.json` | Key points, the subtopic's keyword ids, and "don't confuse" notes. `summaries/index.json` lists the subtopics that have one. |
| `EXTRACTION_NOTES.md` | Where the source PDFs disagree, and decisions taken. |
| `CONTENT_NOTES.md` | Uncertain facts to check, and ordering decisions. |
| `BEYOND_SPEC.md` | Useful things deliberately left out because they aren't on the spec. |

**Rules** (enforced by `tests/test_content.py`): every item's `spec_ids` must exist in
`spec.json`; ids are unique; definitions are one or two sentences; summaries have 4 to 8 key
points; British spelling.

**Verifying.** Every generated item starts as `"verified": false`. When you've checked it, press
**Verify** in the app. That's recorded as an event, so it works straight away on every device. To
make it permanent in the file, set `"verified": true` in the JSON. **Flag as wrong** (with an
optional note) marks an item to fix; flagged items will be kept out of tests.

**Rebuilding `spec.json`** from the PDFs in `spec/`:

```bash
pip install -r tools/requirements-dev.txt
python tools/extract_pdfs.py     # verbatim text -> content/_extracted/
python tools/build_spec.py       # mapping -> content/spec.json (+ _extracted/mapping_report.txt)
```

## Development

```bash
pip install -r requirements-dev.txt
cp .env.example .env   # fill in, then export the variables, e.g. set -a; . ./.env; set +a
DATA_DIR=./data uvicorn --factory app.main:create_app --reload
python -m pytest       # backend and content checks
npm test               # frontend pure modules (Node's built-in test runner; no npm packages)
```

## Dependencies and why

| Dependency | Where | Why |
|---|---|---|
| FastAPI | runtime | Small, typed web framework; request validation via pydantic comes with it. |
| Uvicorn | runtime | The ASGI server that runs FastAPI. |
| pytest, httpx | dev | Test runner; httpx powers FastAPI's test client. |
| pdfplumber | dev (tools only) | Reads table cells, rotated text and link annotations from the spec PDFs. |

Everything else is the Python standard library (sqlite3, hashlib scrypt, hmac) or plain browser
JavaScript. No frontend framework, no build step, no npm packages.

## Project structure

```text
app/
  main.py, config.py, auth.py, db.py, events.py, hashpw.py   FastAPI backend
  static/        index.html, css/app.css, js/ (ES modules: views/, ui/, lib/)
content/         revision content JSON + notes
spec/            the three source PDFs
tools/           PDF extraction and spec.json build scripts
tests/           pytest (backend, content) and tests/js (node --test)
docs/PLAN.md     plan and reasoning for each phase
Dockerfile, docker-compose.yml, .env.example
```
