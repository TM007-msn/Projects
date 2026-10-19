#!/usr/bin/env python3
"""Jarvis room voice for the OptiPlex.

Pipeline (each stage is one function below, so you can test and swap them):

    mic (ReSpeaker XVF3800, echo-cancelled)
      -> wake word      openWakeWord, "hey jarvis"            detect_wake()
      -> record         webrtcvad end-of-speech               record_utterance()
      -> speech-to-text faster-whisper on the CPU             transcribe()
      -> Jarvis         OpenClaw Gateway /v1/chat/completions stream_reply()
      -> text-to-speech Piper, sentence by sentence           synthesize()
      -> speaker        driven from the XVF3800 3.5mm output  Player

Voice turns go into Jarvis's main session (agent:main:main), so something you
say in the room is remembered on Telegram and the other way round.

Extras:
  * Barge-in: saying "hey jarvis" while Jarvis is talking stops it and listens.
  * POST http://127.0.0.1:8765/say {"text": "..."} speaks proactive alerts
    (used by the room-speak skill). Returns 423 during quiet hours or when
    muted. GET /health reports status.
  * If the Gateway can't be reached, it says so and still answers time/date.

Test without a microphone:
  python3 jarvis_voice.py --config config.toml --wav question.wav --out reply.wav
  python3 jarvis_voice.py --config config.toml --text "What's on tomorrow?" --out reply.wav
  python3 jarvis_voice.py --config config.toml --text "hello" --echo   # no Gateway needed
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import os
import queue
import re
import threading
import time
import tomllib
import wave
from dataclasses import dataclass
from datetime import datetime, time as dtime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Iterable, Iterator

log = logging.getLogger("jarvis-voice")

SAMPLE_RATE = 16000  # openWakeWord, webrtcvad and Whisper all want 16 kHz mono
WAKE_FRAME = 1280  # 80 ms: the chunk size openWakeWord is trained on
VAD_FRAME = 480  # 30 ms: one webrtcvad frame


# ===================================================================== config


@dataclass
class Config:
    input_device: str | None = None
    output_device: str | None = None
    wake_model: str = "hey_jarvis"
    wake_threshold: float = 0.5
    silence_ms: int = 700
    max_seconds: float = 15.0
    no_speech_timeout: float = 5.0
    vad_aggressiveness: int = 2
    stt_model: str = "small.en"
    stt_compute_type: str = "int8"
    stt_threads: int = 4
    gateway_url: str = "http://127.0.0.1:18789"
    gateway_token: str = ""
    session_key: str = "agent:main:main"
    message_channel: str = "voice"
    agent: str = "openclaw/main"
    request_timeout: float = 90.0
    piper_model: str = "~/.local/share/piper/en_GB-alan-medium.onnx"
    tts_length_scale: float = 1.0
    server_host: str = "127.0.0.1"
    server_port: int = 8765
    quiet_start: dtime = dtime(23, 30)
    quiet_end: dtime = dtime(7, 0)
    mute_flag: str = "~/.openclaw/workspace/state/voice-muted"


def load_config(path: str | None) -> Config:
    """Read config.toml. The Gateway token comes from the environment
    (OPENCLAW_GATEWAY_TOKEN, loaded from ~/.openclaw/.env by systemd), never the file."""
    data = {}
    if path:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    audio, wake, listen, stt, gw, tts, srv, quiet = (
        data.get(k, {}) for k in ("audio", "wake", "listen", "stt", "gateway", "tts", "server", "quiet_hours"))
    hhmm = lambda v, d: datetime.strptime(v, "%H:%M").time() if v else d  # noqa: E731
    return Config(
        input_device=audio.get("input_device"),
        output_device=audio.get("output_device"),
        wake_model=wake.get("model", "hey_jarvis"),
        wake_threshold=float(wake.get("threshold", 0.5)),
        silence_ms=int(listen.get("silence_ms", 700)),
        max_seconds=float(listen.get("max_seconds", 15)),
        no_speech_timeout=float(listen.get("no_speech_timeout", 5)),
        vad_aggressiveness=int(listen.get("vad_aggressiveness", 2)),
        stt_model=stt.get("model", "small.en"),
        stt_compute_type=stt.get("compute_type", "int8"),
        stt_threads=int(stt.get("cpu_threads", 4)),
        gateway_url=gw.get("url", "http://127.0.0.1:18789").rstrip("/"),
        gateway_token=os.environ.get(gw.get("token_env", "OPENCLAW_GATEWAY_TOKEN"), ""),
        session_key=gw.get("session_key", "agent:main:main"),
        message_channel=gw.get("message_channel", "voice"),
        agent=gw.get("agent", "openclaw/main"),
        request_timeout=float(gw.get("timeout_seconds", 90)),
        piper_model=tts.get("piper_model", Config.piper_model),
        tts_length_scale=float(tts.get("length_scale", 1.0)),
        server_host=srv.get("host", "127.0.0.1"),
        server_port=int(srv.get("port", 8765)),
        quiet_start=hhmm(quiet.get("start"), dtime(23, 30)),
        quiet_end=hhmm(quiet.get("end"), dtime(7, 0)),
        mute_flag=quiet.get("mute_flag", Config.mute_flag),
    )


def in_quiet_hours(now: dtime, start: dtime, end: dtime) -> bool:
    """True if `now` is inside the quiet window (which may wrap past midnight)."""
    if start <= end:
        return start <= now < end
    return now >= start or now < end


def is_muted(cfg: Config) -> bool:
    """Software 'quiet mode' flag. The physical mic mute works on its own: no audio arrives."""
    return Path(cfg.mute_flag).expanduser().exists()


# ===================================================================== text helpers

_SENTENCE_END = re.compile(r"(?<=[.!?])[\"')\]]*\s+|\n+")
_MARKDOWN = re.compile(r"[*_`#>|]+|\[(.*?)\]\((.*?)\)")


def clean_for_speech(text: str) -> str:
    """Strip markdown so Piper doesn't read out asterisks and link syntax."""
    text = _MARKDOWN.sub(lambda m: m.group(1) or "", text)
    text = re.sub(r"https?://\S+", "a link", text)
    return re.sub(r"\s+", " ", text).strip()


class SentenceSplitter:
    """Collects streamed text and hands back whole sentences as soon as they end.

    Speaking sentence by sentence means Jarvis starts talking after the first
    sentence arrives instead of waiting for the whole reply.
    """

    def __init__(self, min_chars: int = 25):
        self.buffer = ""
        self.min_chars = min_chars  # avoids splitting on "e.g. " or "Mr. "

    def feed(self, delta: str) -> list[str]:
        self.buffer += delta
        out = []
        while True:
            match = None
            for m in _SENTENCE_END.finditer(self.buffer):
                if m.end() >= self.min_chars:
                    match = m
                    break
            if not match:
                return out
            sentence, self.buffer = self.buffer[: match.start()], self.buffer[match.end():]
            sentence = clean_for_speech(sentence)
            if sentence:
                out.append(sentence)

    def flush(self) -> list[str]:
        rest, self.buffer = clean_for_speech(self.buffer), ""
        return [rest] if rest else []


def parse_sse(lines: Iterable[str]) -> Iterator[str]:
    """Yield text deltas from an OpenAI-style server-sent-events stream.

    The Gateway reports failures (e.g. expired model login) *inside* the stream
    as `data: {"error": {...}}` after a 200 response, so those raise GatewayError.
    """
    for line in lines:
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            return
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if "error" in chunk:
            err = chunk["error"]
            raise GatewayError(err.get("message", str(err)) if isinstance(err, dict) else str(err))
        for choice in chunk.get("choices", []):
            delta = choice.get("delta") or {}
            if delta.get("content"):
                yield delta["content"]


def local_answer(text: str) -> str | None:
    """Tiny offline fallback: questions answerable without the Gateway."""
    t = text.lower()
    now = datetime.now()
    if "time" in t and "what" in t:
        return f"It's {now.strftime('%H:%M')}."
    if any(k in t for k in ("date", "what day", "today")):
        return f"It's {now.strftime('%A %d %B')}."
    return None


# ===================================================================== gateway


class GatewayError(Exception):
    pass


def stream_reply(cfg: Config, text: str, cancel: threading.Event) -> Iterator[str]:
    """Send one voice turn to Jarvis and yield the reply text as it streams in.

    x-openclaw-session-key puts the turn in Jarvis's main session (shared with
    Telegram). x-openclaw-message-channel tells Jarvis it's a voice turn, so
    AGENTS.md's "Voice replies" rules apply (short, spoken style).
    """
    import httpx

    headers = {
        "Authorization": f"Bearer {cfg.gateway_token}",
        "x-openclaw-session-key": cfg.session_key,
        "x-openclaw-message-channel": cfg.message_channel,
    }
    body = {"model": cfg.agent, "stream": True, "messages": [{"role": "user", "content": text}]}
    try:
        with httpx.stream("POST", f"{cfg.gateway_url}/v1/chat/completions", json=body,
                          headers=headers, timeout=httpx.Timeout(cfg.request_timeout, connect=5)) as r:
            if r.status_code != 200:
                raise GatewayError(f"HTTP {r.status_code}: {r.read()[:200]!r}")
            for delta in parse_sse(r.iter_lines()):
                if cancel.is_set():
                    return
                yield delta
    except httpx.HTTPError as e:
        raise GatewayError(str(e)) from e


# ===================================================================== speech models


class SpeechModels:
    """Loads the heavy models once at start-up (takes a few seconds)."""

    def __init__(self, cfg: Config, need_wake: bool = True, need_stt: bool = True, need_tts: bool = True):
        self.cfg = cfg
        self.wake = self.stt = self.voice = None
        if need_wake:
            from openwakeword.model import Model
            self.wake = Model(wakeword_models=[cfg.wake_model], inference_framework="onnx")
        if need_stt:
            from faster_whisper import WhisperModel
            self.stt = WhisperModel(cfg.stt_model, device="cpu", compute_type=cfg.stt_compute_type,
                                    cpu_threads=cfg.stt_threads)
        if need_tts:
            from piper import PiperVoice
            self.voice = PiperVoice.load(str(Path(cfg.piper_model).expanduser()))


def detect_wake(models: SpeechModels, frame) -> bool:
    """Feed one 80 ms int16 frame; True when the wake word score passes the threshold."""
    scores = models.wake.predict(frame)
    if max(scores.values(), default=0) >= models.cfg.wake_threshold:
        models.wake.reset()  # stop the same utterance triggering twice
        return True
    return False


def record_utterance(cfg: Config, frames: Callable[[], "object"]) -> "object | None":
    """Read frames until you stop talking. Returns float32 audio, or None if you said nothing.

    `frames()` returns the next int16 numpy block from the mic.
    """
    import numpy as np
    import webrtcvad

    vad = webrtcvad.Vad(cfg.vad_aggressiveness)
    audio, pending = [], np.zeros(0, dtype=np.int16)
    started, silent_ms, elapsed = False, 0, 0.0
    while elapsed < cfg.max_seconds:
        block = frames()
        audio.append(block)
        pending = np.concatenate([pending, block])
        while len(pending) >= VAD_FRAME:
            chunk, pending = pending[:VAD_FRAME], pending[VAD_FRAME:]
            elapsed += VAD_FRAME / SAMPLE_RATE
            if vad.is_speech(chunk.tobytes(), SAMPLE_RATE):
                started, silent_ms = True, 0
            elif started:
                silent_ms += 30
        if started and silent_ms >= cfg.silence_ms:
            break
        if not started and elapsed >= cfg.no_speech_timeout:
            return None
    return np.concatenate(audio).astype(np.float32) / 32768.0


def transcribe(models: SpeechModels, audio) -> str:
    segments, _ = models.stt.transcribe(audio, language="en", beam_size=1, vad_filter=False)
    return " ".join(s.text.strip() for s in segments).strip()


def synthesize(models: SpeechModels, text: str):
    """Piper TTS -> (int16 numpy array, sample rate). Works with piper-tts 1.2 and 1.3+."""
    import numpy as np

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        if hasattr(models.voice, "synthesize_wav"):  # piper-tts >= 1.3
            from piper import SynthesisConfig
            models.voice.synthesize_wav(text, wav, syn_config=SynthesisConfig(length_scale=models.cfg.tts_length_scale))
        else:  # piper-tts 1.2
            models.voice.synthesize(text, wav, length_scale=models.cfg.tts_length_scale)
    buf.seek(0)
    with wave.open(buf, "rb") as wav:
        rate = wav.getframerate()
        audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
    return audio, rate


# ===================================================================== playback


class Player:
    """Plays queued speech on its own thread so the mic loop never blocks.
    stop() cuts speech off immediately (barge-in)."""

    def __init__(self, output_device):
        self.q: queue.Queue = queue.Queue()
        self.device = output_device
        self.speaking = threading.Event()
        threading.Thread(target=self._run, daemon=True, name="player").start()

    def say(self, audio, rate: int) -> None:
        self.q.put((audio, rate))

    def stop(self) -> None:
        import sounddevice as sd
        with self.q.mutex:
            self.q.queue.clear()
        sd.stop()

    def _run(self) -> None:
        import sounddevice as sd
        while True:
            audio, rate = self.q.get()
            self.speaking.set()
            try:
                sd.play(audio, rate, device=self.device)
                sd.wait()
            except Exception:  # a bad device shouldn't kill the thread
                log.exception("playback failed")
            finally:
                if self.q.empty():
                    self.speaking.clear()


def chime(rate: int = 22050):
    """Short two-tone 'I'm listening' sound, generated so there's no asset file."""
    import numpy as np
    t = np.linspace(0, 0.09, int(rate * 0.09), endpoint=False)
    tone = np.concatenate([np.sin(2 * np.pi * 880 * t), np.sin(2 * np.pi * 1320 * t)])
    return (tone * 0.25 * 32767).astype(np.int16), rate


# ===================================================================== assistant


class Assistant:
    def __init__(self, cfg: Config, models: SpeechModels, player: Player | None, echo: bool = False):
        self.cfg, self.models, self.player, self.echo = cfg, models, player, echo
        self.cancel = threading.Event()
        self.worker: threading.Thread | None = None
        self.state = "idle"

    def interrupt(self) -> None:
        """Barge-in: stop talking and abandon the reply in progress."""
        self.cancel.set()
        if self.player:
            self.player.stop()
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=2)
        self.cancel = threading.Event()

    def reply_sentences(self, text: str, cancel: threading.Event) -> Iterator[str]:
        """The reply to `text`, sentence by sentence (or a fallback if the Gateway is down)."""
        if self.echo:
            yield f"You said: {text}"
            return
        splitter = SentenceSplitter()
        spoke = False
        try:
            for delta in stream_reply(self.cfg, text, cancel):
                for sentence in splitter.feed(delta):
                    spoke = True
                    yield sentence
            for sentence in splitter.flush():
                spoke = True
                yield sentence
            if not spoke and not cancel.is_set():
                raise GatewayError("empty reply")
        except GatewayError as e:
            log.warning("gateway problem: %s", e)
            if not spoke:  # don't talk over a half-finished answer
                yield local_answer(text) or "I can't reach my main system right now. Try again in a minute, or message me on Telegram."

    def respond(self, text: str, cancel: threading.Event, sink=None) -> dict:
        """Run one turn. Audio goes to the Player, or to `sink` (a list) in test mode."""
        timings, t0 = {}, time.monotonic()
        for sentence in self.reply_sentences(text, cancel):
            if cancel.is_set():
                break
            timings.setdefault("first_sentence_ms", int((time.monotonic() - t0) * 1000))
            audio, rate = synthesize(self.models, sentence)
            timings.setdefault("first_audio_ms", int((time.monotonic() - t0) * 1000))
            log.info("jarvis: %s", sentence)
            if sink is not None:
                sink.append((audio, rate))
            elif self.player:
                self.player.say(audio, rate)
        timings["total_ms"] = int((time.monotonic() - t0) * 1000)
        return timings

    def start_turn(self, text: str) -> None:
        cancel = self.cancel
        self.worker = threading.Thread(target=lambda: log.info("timings %s", self.respond(text, cancel)),
                                       daemon=True, name="turn")
        self.worker.start()


# ===================================================================== /say server


def make_server(cfg: Config, assistant: Assistant) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, obj: dict) -> None:
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                self._send(200, {"ok": True, "state": assistant.state, "muted": is_muted(cfg)})
            else:
                self._send(404, {"ok": False})

        def do_POST(self):  # noqa: N802
            if self.path != "/say":
                return self._send(404, {"ok": False})
            try:
                length = int(self.headers.get("Content-Length", 0))
                text = clean_for_speech(json.loads(self.rfile.read(length) or b"{}").get("text", ""))
            except (ValueError, AttributeError):
                return self._send(400, {"ok": False, "error": "body must be JSON with a 'text' field"})
            if not text:
                return self._send(400, {"ok": False, "error": "empty text"})
            if is_muted(cfg) or in_quiet_hours(datetime.now().time(), cfg.quiet_start, cfg.quiet_end):
                return self._send(423, {"ok": False, "error": "muted or quiet hours"})
            audio, rate = synthesize(assistant.models, text)
            if assistant.player:
                assistant.player.say(audio, rate)
            self._send(200, {"ok": True})

        def log_message(self, fmt, *args):  # keep the journal quiet
            log.debug("http: " + fmt, *args)

    return ThreadingHTTPServer((cfg.server_host, cfg.server_port), Handler)


# ===================================================================== main loops


def find_device(name: str | None, kind: str):
    """Match a device by part of its name (e.g. "XVF3800"); None = system default."""
    if not name:
        return None
    import sounddevice as sd
    for i, dev in enumerate(sd.query_devices()):
        if name.lower() in dev["name"].lower() and dev[f"max_{kind}_channels"] > 0:
            return i
    raise SystemExit(f"No {kind} audio device matching {name!r}. Run: python3 -m sounddevice")


def run_live(cfg: Config, echo: bool) -> None:
    import sounddevice as sd

    models = SpeechModels(cfg)
    player = Player(find_device(cfg.output_device, "output"))
    assistant = Assistant(cfg, models, player, echo=echo)
    server = make_server(cfg, assistant)
    threading.Thread(target=server.serve_forever, daemon=True, name="http").start()

    frames: queue.Queue = queue.Queue(maxsize=200)

    def on_audio(indata, _frames, _time, status):
        if status:
            log.debug("audio status: %s", status)
        try:
            frames.put_nowait(indata[:, 0].copy())
        except queue.Full:
            pass  # drop rather than block the audio thread

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=WAKE_FRAME,
                        device=find_device(cfg.input_device, "input"), callback=on_audio):
        log.info("listening for '%s' (server on %s:%d)", cfg.wake_model, cfg.server_host, cfg.server_port)
        while True:
            frame = frames.get()
            if not detect_wake(models, frame):
                continue
            log.info("wake word")
            assistant.interrupt()  # barge-in if Jarvis was talking
            player.say(*chime())
            assistant.state = "listening"
            audio = record_utterance(cfg, frames.get)
            if audio is None:
                assistant.state = "idle"
                continue
            t0 = time.monotonic()
            text = transcribe(models, audio)
            log.info("heard (%d ms): %s", (time.monotonic() - t0) * 1000, text)
            assistant.state = "idle"
            if text:
                assistant.start_turn(text)
            with frames.mutex:  # don't wake on audio captured while we were busy
                frames.queue.clear()


def run_offline_test(cfg: Config, args) -> None:
    """--wav / --text: run one turn from a file or string and write the reply to a WAV."""
    import numpy as np

    models = SpeechModels(cfg, need_wake=False, need_stt=bool(args.wav))
    timings = {}
    if args.wav:
        with wave.open(args.wav, "rb") as w:
            if w.getframerate() != SAMPLE_RATE or w.getnchannels() != 1:
                raise SystemExit("--wav must be 16 kHz mono (ffmpeg -i in.m4a -ar 16000 -ac 1 out.wav)")
            audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        t0 = time.monotonic()
        text = transcribe(models, audio)
        timings["stt_ms"] = int((time.monotonic() - t0) * 1000)
    else:
        text = args.text
    print(f"you: {text}")
    assistant = Assistant(cfg, models, player=None, echo=args.echo)
    sink: list = []
    timings.update(assistant.respond(text, threading.Event(), sink=sink))
    if args.out and sink:
        rate = sink[0][1]
        with wave.open(args.out, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(np.concatenate([a for a, _ in sink]).tobytes())
        print(f"reply audio: {args.out}")
    print(f"timings: {json.dumps(timings)}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", default=str(Path(__file__).with_name("config.toml")))
    p.add_argument("--wav", help="test: transcribe this 16 kHz mono WAV instead of using the mic")
    p.add_argument("--text", help="test: skip speech-to-text and send this text")
    p.add_argument("--out", help="test: write Jarvis's spoken reply to this WAV")
    p.add_argument("--echo", action="store_true", help="don't call the Gateway; repeat what was heard")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config(args.config if Path(args.config).exists() else None)
    if not cfg.gateway_token and not args.echo:
        log.warning("OPENCLAW_GATEWAY_TOKEN is not set; Gateway calls will fail")
    if args.wav or args.text:
        run_offline_test(cfg, args)
    else:
        run_live(cfg, echo=args.echo)


if __name__ == "__main__":
    main()
