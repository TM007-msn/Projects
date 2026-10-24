# Project plan: a local AI desk assistant with Obsidian as its brain

## Goal

A blueprint to follow once the hardware is in place. The aim is a small touchscreen unit with an all-in-one feel. You tap a button or say a wake word and talk to an AI agent. It shows a character/face you've designed, and it brings up panels on request ("show my calendar" puts the calendar on screen). Everything runs on a local AI machine. Obsidian is the backbone of the whole system: data, memory, config and logs. It isn't a single file store sitting off to the side.

The screenshot that inspired this (`localhost:4320`, "Obsidian as a backend") is a custom web app over an Obsidian vault. This plan uses the same pattern with voice and a character added.

**The core principle:** the vault is the single source of truth. Every other part of the system either reads or writes vault files, or is a cache rebuilt from them. Delete the search index, the app state or even the whole server, and you can rebuild it all from the vault. That's what makes it "a whole system supported by Obsidian".

---

## 1. System architecture

```
 ┌──────────── Desk unit (touchscreen) ────────────┐        ┌──────────── AI machine (Ubuntu server) ────────────┐
 │ Chromium kiosk → Web UI (avatar + panels)       │◄──WS──►│ Orchestrator (Python, FastAPI)                     │
 │ Mic → wake word (openWakeWord) + VAD (Silero)   │──audio►│  ├─ STT: faster-whisper                            │
 │ Speaker ◄───────────────────────────────────────│◄─audio─│  ├─ LLM: Ollama (tool-calling model)               │
 │ Physical/onscreen "talk" button                 │        │  ├─ TTS: Piper or Kokoro                           │
 └─────────────────────────────────────────────────┘        │  ├─ Tools: calendar, tasks, notes, revision, server│
                                                            │  ├─ Vault indexer (watchdog + embeddings)         │
                                                            │  └─ MCP server (vault tools, for Claude etc.)     │
                                                            │                                                    │
                                                            │ Obsidian vault (Markdown files) ◄── Syncthing ──► PC / phone Obsidian
                                                            │   └─ git auto-commit = history + undo              │
                                                            └────────────────────────────────────────────────────┘
```

**The flow of one request:** wake word fires → UI switches the avatar to *listening* → audio streams to the server → VAD detects you've stopped talking → Whisper transcribes → the orchestrator sends the text, persona and relevant vault context to the LLM → the LLM replies with speech and/or **tool calls** (`show_panel("calendar", "this_week")`, `create_task(...)`) → tools read or write the vault → the orchestrator pushes UI events over WebSocket → TTS streams audio back while the avatar lip-syncs.

**Why a custom orchestrator rather than Home Assistant Assist:** HA's voice pipeline (Wyoming protocol, the same Whisper/Piper/openWakeWord parts) is the shortcut if you only want voice control. It doesn't give you a custom character UI or a vault-centred memory, and building the orchestrator yourself is the valuable part for a CS/cyber portfolio. You'd still reuse the same open-source components, and you could add HA later as one more tool.

---

## 2. Hardware

Prices are rough UK figures from my training data. Check them before buying.

| Part | Recommendation | Why | Approx. |
|---|---|---|---|
| AI machine | Your existing Ubuntu server **if** it can take a GPU with ≥12 GB VRAM (used RTX 3060 12 GB is the budget sweet spot) | 8–14B models plus Whisper fit comfortably and reply quickly | £180–250 for the GPU |
| Alternative AI machine | Mac mini (Apple silicon, 16 GB+) | Quiet, low power, good at local LLMs, but not Ubuntu/Docker-native for GPU work | ~£600 |
| Desk unit | Raspberry Pi 5 (4 GB) + **Raspberry Pi Touch Display 2** (7", 720×1280) | Runs a kiosk browser and wake word easily, with an official case/stand ecosystem | ~£60 + ~£60 |
| Mic | USB conference mic or a ReSpeaker-style mic array | Far-field pickup matters more than anything else for a voice assistant | £20–50 |
| Speaker | Small USB/3.5 mm powered speaker | | £15–30 |
| Button (optional) | Arcade button on Pi GPIO | A satisfying physical "talk" button, and a privacy-friendly alternative to always-on wake word | £5 |

Keep the Pi thin: it handles only display, mic, speaker and wake word, and all the heavy compute stays on the server. You can later add a second screen (a tablet in kiosk mode) with no extra server work.

---

## 3. Software stack (all free/open-source, self-hostable)

| Layer | Choice | Notes |
|---|---|---|
| Wake word | **openWakeWord** | Can train a custom wake word on your assistant's name |
| End-of-speech | **Silero VAD** | Detects when you stop talking |
| Speech-to-text | **faster-whisper** (`small`/`medium`, English) | Runs on GPU, near-instant |
| LLM runtime | **Ollama** | A current ~8–14B model with good tool calling (e.g. the Qwen3 family at time of writing). Swap models freely |
| Embeddings | Ollama `nomic-embed-text` (or similar) | For "search my notes by meaning" |
| Vector index | **sqlite-vec** or LanceDB | A single file and rebuildable from the vault, so it counts as a cache |
| Text-to-speech | **Piper** (fast, many voices) or **Kokoro** (more natural) | Voice choice is part of your character |
| Orchestrator | **Python + FastAPI + WebSockets** | Your main code. Python because every AI library above is Python |
| UI | **Plain HTML/CSS/JS or Svelte**, served by the orchestrator | Runs in `chromium --kiosk` on the Pi |
| Avatar | **Rive** (state-machine animation, web runtime) | Alternatives: Live2D for an anime-style character, or a hand-made SVG/CSS face to start |
| Sync | **Syncthing** (vault ↔ PC ↔ phone) | Plus a git auto-commit on the server |
| Calendar | Events as **vault notes** (Obsidian *Full Calendar* plugin format) | Optional: Radicale (self-hosted CalDAV), or a one-way import from Google Calendar via ICS |
| Remote access | **Tailscale** or WireGuard | Never port-forward any of this |

---

## 4. The vault as the operating system

The vault does four jobs: **data** (calendar, tasks, notes), **config** (the agent's personality and settings), **memory** (what the agent has learnt about you) and **logs** (what it did). Editing a note in Obsidian on your phone changes how the assistant behaves. That's the "everything in one place" payoff.

```
vault/
├─ 00 Home/            Home.md: the Obsidian-side dashboard (Bases/Dataview)
├─ 01 Daily/           2026-10-24.md: daily note; the agent appends a summary of the day's conversations
├─ 02 Calendar/        one note per event (frontmatter: date, startTime, endTime, location)
├─ 03 Tasks/           tasks with due dates (Tasks plugin syntax), queryable everywhere
├─ 10 Revision/        CS H446 and Maths 9MA0, one note per spec topic: confidence, last_reviewed, flashcards
├─ 20 Applications/    one note per uni/apprenticeship: deadline, status, route
├─ 30 Projects/        incl. this assistant project itself
├─ 40 Server/          one note per Docker service: port, compose path, health URL
├─ 50 People/          contacts the agent can reference ("remind me to message X")
├─ 60 Reading/         articles and links captured by voice or phone
├─ 80 Agent/
│   ├─ Persona.md      name, personality, speaking style, voice id, avatar skin, wake word
│   ├─ Settings.md     panels enabled, quiet hours, confirmation rules, model name
│   ├─ Memory/         facts the agent learnt ("Taylor prefers revision in the morning"); one note each, editable/deletable by you
│   ├─ Skills/         one note per tool/routine in plain English ("Morning briefing: read calendar, tasks due, weakest revision topic")
│   └─ Logs/           per-day conversation transcripts and tool calls (audit trail)
├─ 90 Templates/
└─ 99 Inbox/           anything the agent creates lands here first for you to file or approve
```

**Rules that keep it from turning into a mess** (and why the old attempts went back to plain note-taking):
- Every structured note uses **frontmatter properties** (`type: event|task|topic|application|memory`). The orchestrator, Obsidian Bases and the kiosk UI all query the same fields.
- The agent **never silently edits your notes**. It creates notes in `99 Inbox/` or appends under a `## From assistant` heading, and every write is a git commit, so you can always see and undo it.
- **Persona and Settings live in Markdown**, so you tune the character in Obsidian with no code changes.
- **Memory is visible.** If the agent "remembers" something wrong, you delete the note. No hidden database.

**Obsidian-side plugins** (for when you're at the PC): Bases (core), Dataview, Templater, Tasks, Full Calendar, Homepage, QuickAdd, Spaced Repetition, Excalidraw, Obsidian Git (on PC only, if the server doesn't already commit), Minimal theme + Style Settings.

---

## 5. Touchscreen interface design

**Screen states, which are also the avatar's animation states:**
1. **Ambient/idle:** large clock and date, the avatar idling (breathing, blinking), next event, today's top 3 tasks, and a dimmed screen at night (quiet hours from `Settings.md`).
2. **Listening:** avatar attentive, live waveform, partial transcript shown as you speak.
3. **Thinking:** avatar "processing" animation and the names of tools being called ("checking calendar…"). This is a nice transparency touch.
4. **Speaking:** avatar lip-sync driven by the TTS audio amplitude, with the reply text in a caption bar.
5. **Panel:** the avatar shrinks to a corner and a full panel slides in, dismissable by tap, by voice ("close that") or by timeout.

**Panels (each one is a vault query rendered nicely):**
- **Calendar:** day/week strip like the screenshot, from `02 Calendar/`
- **Tasks:** due/overdue, tap to complete, which writes back to the vault
- **Revision:** weakest topics by `confidence`, flashcards due today, a "quiz me" button that starts a spoken flashcard session
- **Applications:** deadlines countdown and status board
- **Server:** container health from `40 Server/` health URLs (green/red tiles)
- **Notes/search:** "what did I write about recursion?" shows the matched notes plus a summary
- **Timer/focus:** Pomodoro that logs sessions to the daily note
- **Weather/news feed:** optional and needs internet; keep it clearly separated from local data

**Bottom dock** (like the screenshot): Home · Calendar · Tasks · Revision · Server · Talk (big button). Touch and voice reach the same panels, because both go through the same `show_panel` event.

**How "show my calendar" works technically:** the LLM gets a tool `show_panel(name, args)`. When it calls it, the orchestrator sends `{"type":"panel","name":"calendar","range":"week"}` over the WebSocket and the UI renders it. The LLM never draws UI. It only chooses which panel to show and with what arguments, which is reliable even with small local models.

---

## 6. Agent design

- **System prompt** = `Persona.md` + `Settings.md` + today's date, next events and due tasks (a small "situational awareness" block) + the top-k relevant vault chunks for the question (RAG).
- **Tools**, with permission tiers set in `Settings.md`:
  - *Read (automatic):* `get_events`, `get_tasks`, `search_notes`, `get_revision_status`, `server_health`
  - *Write (automatic, into Inbox/append-only):* `create_task`, `create_event`, `capture_note`, `log_study_session`, `remember_fact`
  - *Confirm first (spoken "yes" or tap):* edit/delete existing notes, anything touching the server (restart a container), anything sending data off the machine
- **Routines** defined in `80 Agent/Skills/`: morning briefing, end-of-day summary into the daily note, a weekly revision report, deadline warnings.
- **MCP server:** expose the same vault tools over MCP so Claude Desktop or other agents can use your vault too, with one tool layer and many front-ends.

---

## 7. Security (worth doing properly; it's a cyber portfolio talking point)

- Everything binds to the LAN/Tailscale only, with an API key between Pi and server, and no port-forwarding.
- **Prompt injection:** content the agent reads (web pages, imported emails, notes you clipped) can contain instructions. Treat tool results as data, keep write/confirm tiers enforced **in code, not in the prompt**, and log every tool call to `80 Agent/Logs/`.
- Microphone privacy: a hardware mute (or button-only mode), a visible "listening" indicator, and no audio stored by default (transcripts only, deletable).
- The vault is backed up off-machine (encrypted, e.g. restic to another disk) because it holds personal data.

---

## 8. Build roadmap (milestones with "done when" criteria)

Each milestone is usable on its own, so you can stop at any point and still have something that works.

| # | Milestone | Done when |
|---|---|---|
| M0 | **Vault foundation.** The structure above, templates, the Home dashboard, used daily in plain Obsidian for 2 weeks | You open it every day without thinking. Fix the habit before building tech on top of it |
| M1 | **Sync + server.** Syncthing on the Ubuntu server (Docker), git auto-commit, Tailscale | Edit on phone → appears on server → committed |
| M2 | **Text agent.** Ollama + orchestrator with read tools over the vault, chatting via a basic web page | "What's due this week?" gives a correct answer from vault notes |
| M3 | **Kiosk UI.** Avatar (simple SVG first) + panels + dock on the Pi touchscreen, driven by WebSocket events | Tapping the dock and typed commands both open the correct panels |
| M4 | **Voice.** Wake word, VAD, Whisper and Piper wired in, with lip-sync from audio amplitude | Saying "Hey <name>, show my calendar" opens the calendar and answers aloud in < ~2–3 s |
| M5 | **Write tools + memory.** Create tasks/events, remember facts, confirmation flow, logs | Spoken "add a task to do a 9MA0 paper Friday" appears in Obsidian with a git commit |
| M6 | **Routines + RAG.** Morning briefing, revision quiz mode, semantic note search | Morning briefing runs on schedule, and "quiz me on Big-O" pulls your own flashcards |
| M7 | **Polish.** Rive/Live2D character, custom wake word, physical button, case/stand, MCP server | You'd be happy to demo it in an interview |

**Timing:** M0 costs nothing and helps your resit revision right now. M1–M3 are a good half-term project. Keep M4+ for after exams or the summer, so it doesn't eat into revision time in the run-up to your 2027 papers.

---

## 9. Open decisions (to settle when you start)

1. **Server GPU:** what's in the Ubuntu server now? This decides whether you need a GPU upgrade or a separate AI box.
2. **Calendar source of truth:** vault-only (simplest, fully local) or keep Google Calendar and import one-way. Recommendation: **vault-only**, with an ICS import for school/exam dates.
3. **Character style:** simple geometric face (fastest), Rive cartoon, or Live2D anime-style. Recommendation: start with **SVG/CSS** in M3 and upgrade in M7.
4. **Assistant's name and voice:** this sets the wake-word training and the Piper/Kokoro voice.
