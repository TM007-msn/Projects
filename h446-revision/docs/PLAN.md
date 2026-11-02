# H446 Revision App: Plan

This file is updated before each phase. Older phases stay here so the reasoning is traceable.

## Overall shape (all phases)

- **Location:** `h446-revision/` inside the `Projects` repo.
- **Backend:** Python 3.12, FastAPI, SQLite (one file on a mounted volume). Stores progress only.
- **Frontend:** vanilla HTML/CSS/JS ES modules, no build step, served by FastAPI as static files.
- **Content:** versioned JSON in `content/`. `spec.json` is the spine; every other content item
  carries `spec_ids` pointing into it, and a build-time check rejects any item whose `spec_ids`
  are not in `spec.json`.
- **Progress model (Phase 1 onwards):** append-only `events` table (client-generated UUID, client
  timestamp, type, payload). Current state (ratings, SM-2 card state, mastery) is derived by
  replaying events, so offline sync in Phase 6 is "insert events you don't already have", which is
  idempotent by UUID.

---

## Phase 0: extract the spec

### Goal

`content/spec.json` with every spec point: id, component/paper, topic, subtopic, spec wording,
clarification text, mapped checklist statements, cross-topic links and resource URLs, taken word
for word from the two PDFs. No app code.

### What the PDFs actually look like (this drives the design)

- **OCR guide (24 pages):** one table row per **subtopic** (e.g. 1.1.1). Column 1 lists the
  lettered points (a, b, c...). Column 2 is the clarification, written as paragraphs for the
  subtopic as a whole, not per letter. Column 3 holds cross-topic links and resource URLs, also per
  subtopic. Two subtopics (2.2.1, 2.3.1) continue onto a second page.
- **Craig'n'Dave checklist (21 pages):** 25 numbered topics (1 to 26, no 25), each roughly one OCR
  subtopic, each a list of "Candidates need to..." statements. The statements are mostly the OCR
  clarification text cut into sentences, with some additions and omissions.

So the per-point clarification and per-point checklist mapping do not exist in the sources. They
have to be inferred, and that inference must be visible and correctable.

### Approach

Two scripts, so extraction (mechanical) is separate from mapping (judgement):

1. `tools/extract_pdfs.py` (pdfplumber) writes verbatim intermediates to `content/_extracted/`:
   - Guide: table cells per row; the sideways subtopic title is read from rotated characters;
     paragraphs are split on vertical gaps (≈2.0pt within a paragraph, ≈4.8pt between);
     lettered points are split on `a)`, `b)`...; bullet lines are kept as separate lines.
   - Checklist: statement rows are found from the alternating row fills (only every other row is
     filled, so unfilled rows are the gaps between fills); topic headers, video links, paper
     headings and "Additional notes" are recognised by their text.
2. `tools/build_spec.py` builds `content/spec.json`:
   - `PARAGRAPH_POINTS`: a hand-written table saying which point letter(s) each clarification
     paragraph belongs to. Every point gets `"clarification_mapping": "inferred"` and
     `clarification_shared_with` listing other points that share its paragraphs.
   - Checklist statements are matched automatically to the clarification paragraph sharing the
     most words (≥75% of the statement's words), inheriting that paragraph's letters.
     `STATEMENT_OVERRIDES` fixes the 46 statements where that is wrong or too coarse.
   - `content/_extracted/mapping_report.txt` lists every statement with its match score and how it
     was mapped, so the mapping can be audited line by line.
   - Resource URLs use the URL **as printed** (word for word). The PDF's clickable link targets
     sometimes differ; those differences go in the report, not the data.

### Data model: `content/spec.json`

```text
{
  schema_version, generated_by, sources, notes,
  papers:    [{paper, component, checklist_heading}],
  topics:    [{id "1.1", component, paper, title, heading}],
  subtopics: [{id "1.1.1", topic, title, clarification[], cross_topic_links[{id,label}],
               resource_urls[], checklist_topic{topic_number,title,video_url,additional_notes},
               guide_pages[], point_ids[]}],
  points:    [{id "1.1.1a", component, paper, topic, topic_title, subtopic, subtopic_title,
               letter, spec_wording, clarification[], clarification_mapping,
               clarification_shared_with[], checklist_statements[{id,text}],
               cross_topic_links[], resource_urls[], video_url}],
  checklist_unmapped: []
}
```

Points repeat their subtopic's links and URLs so the app can render a point without a join.
Checklist statement ids (`cl-TT-NN`) are stable as long as the PDF doesn't change.

### Risks and how they're handled

| Risk | Mitigation |
|---|---|
| Wrong text extraction (merged columns, lost hyphens, reversed sideways text) | Verified every point's wording and every clarification sentence is present in an independent `pdftotext -raw` dump. The only differences are pdftotext dropping spaces around curly quotes. Visual spot checks of row counts on several checklist pages. |
| Wrong paragraph-to-point mapping | Mapping is a small, readable table in `build_spec.py`; flagged as inferred in the data; shared paragraphs listed per point. |
| Wrong statement-to-point mapping | Score per statement in `mapping_report.txt`; all multi-point and low-score matches reviewed by hand and overridden where needed. |
| PDFs out of date vs the live spec | Can't be checked from the PDFs alone. Flagged in `EXTRACTION_NOTES.md` for Taylor. |
| Content referenced but not in the PDFs (Appendix 5d/5g) | Flagged; no content invented. |

### Not done in Phase 0

No keywords, summaries or app code.

---

### Phase 0 addendum (after review)

Taylor added the H446 specification (Version 3.0, April 2026). `tools/extract_pdfs.py` now also
reads section 2c by splitting each text row at the column boundary (x≈292pt; rows whose words cross
it are full-width headings). `spec_wording` comes from the specification, `guide_wording` is kept.
Appendix 5d/5f is hand-transcribed in `tools/appendix_5d_5f.json` (the Boolean symbols don't survive
text extraction, so they were read from the page images). Bulleted points 1.3.3b, 1.5.2a and
2.2.2f gained `sub_items`.

---

## Phase 1: skeleton, spec tracker, topic 1.1 content

### Files

```text
app/
  main.py        FastAPI app: routes, static files, content route
  config.py      env vars, validated at start-up
  auth.py        scrypt password check, HMAC-signed session cookie, login rate limit
  db.py          SQLite connection, schema + migrations (PRAGMA user_version)
  events.py      /api/events: validate and insert-or-ignore
  hashpw.py      CLI: python -m app.hashpw  -> prints a hash for APP_PASSWORD_HASH
  static/        index.html, css/app.css, js/ (ES modules, see below), icons
content/
  spec.json, keywords.json, summaries/1.1.1.json ... 1.1.3.json
  CONTENT_NOTES.md, BEYOND_SPEC.md
tests/           pytest: auth, events, content validation
tests/js/        node --test: pure frontend modules
Dockerfile, docker-compose.yml, .env.example, requirements.txt, requirements-dev.txt
```

Frontend modules: `main.js` (boot + hash router), `api.js` (fetch helpers), `store.js` (content
and events in memory, optimistic writes), `lib/derive.js` (pure: ratings, flags, verification from
events), `lib/dom.js` (tiny element builder; all user text goes in via `textContent`), `views/`
(login, home, spec map, summary), `ui/` (verify/flag controls, theme toggle).

### Data model

**SQLite: one append-only table.**

```sql
CREATE TABLE events (
  id          TEXT PRIMARY KEY,  -- UUID made on the device
  client_ts   TEXT NOT NULL,     -- ISO 8601 with offset, from the device
  received_at TEXT NOT NULL,     -- server UTC, also the sync cursor in Phase 6
  type        TEXT NOT NULL,     -- rating | verify | unverify | flag | unflag
  target      TEXT NOT NULL,     -- spec point / sub-item id, or content item id
  data        TEXT NOT NULL      -- JSON, e.g. {"value":"got"} or {"note":"..."}
);
```

`POST /api/events` takes a batch and uses `INSERT OR IGNORE`, so resending the same events (retry,
offline queue) is harmless. Nothing is ever updated or deleted. Current state is derived on the
client: for each target, the event with the latest `client_ts` (ties broken by id) wins.

- **Ratings:** `need` / `once` / `got` per point or sub-item. Last-reviewed date = that event's
  `client_ts`. A point with sub-items isn't rated directly: it shows the lowest sub-item rating and
  "n of m rated".
- **Verification:** the JSON's `verified` flag, or a later `verify` event without a later
  `unverify`. A script to write verifications back into the JSON comes with the README.
- **Flags:** `flag` with an optional note; `unflag` clears it. Flagged items get a badge now and
  are excluded from tests in Phase 5.

**Content JSON.** `keywords.json` follows Taylor's example entry (id, term, acronym, definition,
spec_ids, related, dont_confuse_with, verified), plus optional `"source": "checklist"`. Each
`summaries/<subtopic>.json` holds 4 to 8 `key_points` (id, text, spec_ids, verified), the
subtopic's `keyword_ids`, and `dont_confuse` notes (id, text, keyword ids, spec_ids, verified).
Resource links aren't copied: the page reads them from `spec.json`.

### Auth

- `APP_PASSWORD_HASH`: scrypt (stdlib `hashlib`), stored as `scrypt:n:r:p:salt:hash` with
  base64url parts. No `$` signs, because Docker Compose treats `$` in `.env` as a variable.
- Session cookie: `expiry.signature` with HMAC-SHA256 using `SECRET_KEY`; HttpOnly, SameSite=Lax,
  `Secure` when `COOKIE_SECURE=true`. Stateless, so changing `SECRET_KEY` logs out every device.
- CSRF: SameSite=Lax plus POSTs must be `application/json` (a cross-site form can't send that
  without a CORS preflight, and no CORS is enabled).
- Login rate limit: 5 failures per IP per 15 minutes, in memory.
- Public: `/`, static assets, `/api/health`, `/api/login`. Everything under `/api` and `/content`
  needs the cookie.

### Order of work

1. Backend + pytest (auth, events, idempotency).
2. Docker and compose.
3. Frontend shell, login, spec map with ratings.
4. 1.1 keywords and summaries, then the summary page (read mode and cover mode).
5. Content validation test, browser check at phone width, commit.

### Risks

| Risk | Mitigation |
|---|---|
| Inaccurate definitions (the biggest risk) | Mark-scheme style, PDF wording where it exists, `verified:false`, flag button, uncertainties listed in `CONTENT_NOTES.md`. Anything beyond the spec goes to `BEYOND_SPEC.md`. |
| Content that goes beyond the spec | Validation test: every `spec_ids` entry must exist in `spec.json`. |
| Cookie forgery / auth bypass | HMAC with `compare_digest`; a test confirms every protected route returns 401 without the cookie. |
| Path traversal on `/content/...` | Resolve the path and reject anything outside the content dir; tested. |
| Device clocks disagree, so the wrong rating "wins" | Acceptable for one user; ties broken deterministically. Noted for Phase 6. |
| XSS through flag notes | Notes rendered with `textContent` only. |
| US spellings creeping in | Content test rejects a list of common US spellings in prose fields. |

### Found during Phase 1 (affects later phases)

- **Phase 6 needs HTTPS for offline use.** Service workers (required for an installable PWA and
  offline caching) only run in a secure context: HTTPS or `localhost`. Plain `http://<lan-ip>` won't
  work. The simplest free option is `tailscale serve`, which gives the server a real HTTPS
  certificate on its Tailscale name. `crypto.randomUUID()` has the same restriction, which is why
  event ids are built from `crypto.getRandomValues()`.
- Until Phase 6, the offline queue is a small `localStorage` list: ratings made with no signal are
  kept and resent automatically (shown as "n changes waiting to sync").

---

## Phase 2: remaining content

### Goal

Keywords and summaries for 1.2 to 2.3 (21 subtopics), one topic per commit, in the 1.1 style.
No corrections to 1.1 have been made yet (Taylor hasn't reviewed it), so the 1.1 style is
carried forward unchanged. If the review finds a systematic problem, fix it across all topics in
one pass.

### Data model changes

- Optional keyword fields:
  - `"source": "checklist"` for items that exist only because of the Craig'n'Dave checklist
    (decision 3 in EXTRACTION_NOTES).
  - `"alternative_acronyms": [...]` for the LMC mnemonics OCR also accepts (STO, LOAD, BR, BZ,
    BP, IN/INPUT, COB/END), so typed answers in Phase 4/5 can accept them.
- Keywords can reference sub-item ids (e.g. `1.5.2a.3`) in `spec_ids`.
- One keyword per concept, even when it's on two spec points (e.g. Abstraction is 2.1.1 and
  2.2.2e). When two concepts share a word, the term says which is meant: "Normalisation
  (floating point)" vs "Normalisation (databases)", "Record (data structure)" vs "Record
  (database)", "Pipelining (problem solving)" vs the processor's "Pipelining".

### New content checks

- Every keyword appears in at least one summary (so nothing is unreachable).
- Optional fields have the right types.

### Risks

| Risk | Mitigation |
|---|---|
| Words with two spec meanings ("redundancy" in 1.3.2f is fault tolerance, not data redundancy; "pipelining" in 1.1.1d vs 2.2.2f) | Separate, disambiguated keywords plus "don't confuse" notes. |
| Algorithm facts stated wrongly (Big O cases, preconditions) | Only standard, uncontroversial complexities; anything implementation-dependent (e.g. Dijkstra's Big O) left out and noted. |
| Orderings that sources disagree on (waterfall stages, compilation optimisation) | Noted in CONTENT_NOTES now, before Phase 4 builds ordering items. |
| Volume (about 250 keywords) makes errors likely | Everything stays unverified; uncertainties listed per topic in CONTENT_NOTES. |
