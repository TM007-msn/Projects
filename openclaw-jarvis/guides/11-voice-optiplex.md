# 11 · Room voice on the OptiPlex (now)

**What:** say "Hey Jarvis" anywhere in your room and get a spoken answer from the same Jarvis you text. Jarvis can also speak alerts out loud when you're home.
**Why now, on the OptiPlex:** OpenClaw's native Voice Wake/Talk exists only in the macOS, iOS and Android apps. The Linux desktop app has none, and the big box is months away. A small Python daemon on the OptiPlex gets you voice today with hardware you already own.

## The pipeline

```
ReSpeaker XVF3800 mic ──► openWakeWord "hey jarvis" ──► chime ──► record until you stop (webrtcvad)
     (echo-cancelled)                                                     │
                                                                          ▼
 XVF3800 3.5mm out ◄── Piper TTS (British voice) ◄── sentence ◄── Gateway /v1/chat/completions (streamed)
   → powered speaker      sentence by sentence           splitter        session agent:main:main, channel "voice"
                                                                          ▲
                                                           faster-whisper small.en (int8, CPU)
```

- **One identity:** the daemon sends each turn with `x-openclaw-session-key: agent:main:main`, the same conversation as your Telegram DMs. Ask by voice, follow up on Telegram.
- **Spoken style:** `x-openclaw-message-channel: voice` triggers the "Voice replies" rules in `AGENTS.md` (short, no markdown or URLs).
- **Barge-in:** wake detection keeps running while Jarvis talks. "Hey Jarvis" cuts it off and listens again.
- **Proactive speech:** `POST http://127.0.0.1:8765/say` (used by the `room-speak` skill). It refuses (423) during quiet hours (23:30–07:00) or when muted.
- **Offline:** if the Gateway or cloud model is unreachable, it says so and still answers "what time is it" and "what's the date". A useful offline Jarvis needs the local model (guide 12).

Code: `voice/jarvis_voice.py` (heavily commented, one function per stage), config `voice/config.example.toml`, tests `voice/tests/`.

## Hardware

1. **ReSpeaker XVF3800 → OptiPlex by USB.** Check it appears: `arecord -l` and `python3 -m sounddevice`.
2. **Speaker:** plug a **powered speaker with a 3.5mm/line input** into the **XVF3800's 3.5mm output**, not the OptiPlex's jack. This is what lets the XVF3800's echo canceller subtract Jarvis's own voice, so barge-in works and Jarvis doesn't wake itself up. Your spec's "Siren N200" is unverified, so any £20–50 powered desktop speaker with an AUX input works.
3. **Placement:** the OptiPlex has to be within USB-cable reach of where the mic sits (up to 5 m with a decent cable; use an active extension beyond that). If the OptiPlex lives elsewhere, see *Satellite option* below.
4. **Hard mute (privacy requirement):** use the XVF3800's mute control if your board has one, otherwise an inline USB switch on the mic cable. When it's off, no audio reaches software, so nothing can override it. There's also a soft "quiet mode": `touch ~/.openclaw/workspace/state/voice-muted` (and `rm` it to undo).

Check the exact XVF3800 board revision and its firmware's USB audio mode (it needs the USB-audio firmware rather than I2S). Seeed's wiki has the flashing steps if `arecord -l` doesn't list it.

## Install (about 45 minutes)

```bash
sudo apt install -y libportaudio2 python3-venv
python3 -m venv ~/.venvs/jarvis-voice
~/.venvs/jarvis-voice/bin/pip install -r ~/openclaw-jarvis/voice/requirements.txt
# openWakeWord 0.6 insists on tflite-runtime, which has no wheels for Python 3.12+.
# We use its ONNX backend, so install it without that dependency:
~/.venvs/jarvis-voice/bin/pip install --no-deps openwakeword==0.6.0

# Wake word model
~/.venvs/jarvis-voice/bin/python -c "import openwakeword.utils as u; u.download_models(model_names=['hey_jarvis'])"

# A British Piper voice (about 60 MB). Alternatives: northern_english_male, jenny_dioco, cori
mkdir -p ~/.local/share/piper && cd ~/.local/share/piper
for f in en_GB-alan-medium.onnx en_GB-alan-medium.onnx.json; do
  curl -LO "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/$f"; done

# Config
cd ~/openclaw-jarvis/voice && cp config.example.toml config.toml   # edit device names if needed
```

Enable the Gateway endpoint the daemon talks to (already in the example config):
`gateway.http.endpoints.chatCompletions.enabled: true`, then `openclaw gateway restart`. The Gateway stays bound to loopback, and the daemon runs on the same machine.

## Test without the mic, then with it

```bash
cd ~/openclaw-jarvis/voice && set -a && . ~/.openclaw/.env && set +a
PY=~/.venvs/jarvis-voice/bin/python
$PY jarvis_voice.py --text "hello" --echo --out /tmp/echo.wav        # TTS only, no Gateway
$PY jarvis_voice.py --text "What's my next commitment?" --out /tmp/r.wav   # Gateway + TTS, prints timings
aplay /tmp/r.wav
$PY jarvis_voice.py -v                                                # live: say "Hey Jarvis…"
```

The first live run downloads the Whisper model (`small.en`, about 500 MB). Then install the service:

```bash
mkdir -p ~/.config/systemd/user && cp jarvis-voice.service ~/.config/systemd/user/
systemctl --user daemon-reload && systemctl --user enable --now jarvis-voice
journalctl --user -u jarvis-voice -f
```

## Latency: what to expect and how to tune it

Your spec's target is 2–4 seconds (Alexa-like). On the OptiPlex 7060's CPU, a typical turn breaks down roughly as:

| Stage | Typical | Tune |
|---|---|---|
| End-of-speech detection | 0.7 s | `silence_ms` 500–700 (lower cuts you off mid-pause) |
| Whisper `small.en` int8, 3–5 s of speech | 1–2 s | `base.en` is about twice as fast, slightly less accurate |
| Gateway → first sentence from Claude | 1–2.5 s | Short spoken replies (AGENTS.md); Sonnet rather than Opus |
| Piper, first sentence | 0.2–0.4 s | `medium` voices; avoid `high` |
| **Wake → first audio** | **about 3–5 s** | |

The `--text`/`--wav` test modes print `stt_ms`, `first_sentence_ms`, `first_audio_ms` and `total_ms`, so measure on your box. Two levers if it's too slow:
1. `stt.model = "base.en"` (biggest win).
2. Cloud STT (e.g. Groq's hosted Whisper) is faster, but your voice leaves the house. That's a privacy trade-off, so only do it if local is unbearable.

Moving to the Mac Studio / DGX / Strix box (guide 12) brings Whisper well under 0.5 s.

## Satellite option (if the OptiPlex isn't in your room)

Run the same daemon on a Raspberry Pi 5 (8GB) next to the mic, pointed at the OptiPlex Gateway over Tailscale (`gateway.url`). `base.en` is the realistic Whisper size on a Pi. This costs about £80 and is only worth it if moving the OptiPlex isn't an option.

## Why not Home Assistant + Wyoming?

It uses the same engines (openWakeWord, faster-whisper, Piper) and is very polished. But it's a whole extra system to run and update, for a smart-home integration you rated 2/10. Your own ~400-line Python daemon is easier to debug, and it talks to Jarvis directly.

## Verify

- [ ] `python3 -m pytest voice/tests` passes
- [ ] "Hey Jarvis, what's on tomorrow?" from 3 m away → a spoken answer in under 5 seconds
- [ ] Interrupt mid-answer with "Hey Jarvis" → it stops and listens
- [ ] Ask by voice, then on Telegram ask "what did I just ask you out loud?" → it knows
- [ ] `curl -X POST 127.0.0.1:8765/say -d '{"text":"test"}'` speaks (and returns 423 after 23:30)
- [ ] Hardware mute on → wake word does nothing
