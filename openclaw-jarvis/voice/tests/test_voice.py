"""Tests for the parts of jarvis_voice.py that don't need a microphone or models.

Run:  python3 -m pytest voice/tests
"""

import json
import sys
import threading
from datetime import time as dtime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import jarvis_voice as jv  # noqa: E402


# ------------------------------------------------------------------ sentences


def test_splitter_emits_sentences_as_they_complete():
    s = jv.SentenceSplitter()
    out = []
    for piece in ["Morning, Taylor. It's", " 06:48 on Tuesday. ", "Want the full", " briefing?"]:
        out += s.feed(piece)
    assert out == ["Morning, Taylor. It's 06:48 on Tuesday."]
    assert s.flush() == ["Want the full briefing?"]


def test_splitter_does_not_split_short_abbreviations():
    s = jv.SentenceSplitter()
    assert s.feed("e.g. maths ") == []
    assert s.feed("and economics revision tonight. Next") == ["e.g. maths and economics revision tonight."]


def test_clean_for_speech_strips_markdown_and_urls():
    text = "**Done.** See [the doc](https://x.y/z) or https://example.com `now`"
    assert jv.clean_for_speech(text) == "Done. See the doc or a link now"


# ------------------------------------------------------------------ SSE parsing


def sse(*deltas, done=True):
    lines = [f"data: {json.dumps({'choices': [{'delta': {'content': d}}]})}" for d in deltas]
    lines.insert(0, ": keep-alive")
    lines.append('data: {"choices":[{"delta":{}}]}')
    if done:
        lines.append("data: [DONE]")
    lines.append("data: ignored-after-done")
    return lines


def test_parse_sse_yields_content_and_stops_at_done():
    assert list(jv.parse_sse(sse("Hello", " there."))) == ["Hello", " there."]


def test_parse_sse_raises_on_in_stream_error():
    # Shape copied from a real OpenClaw 2026.10.5 Gateway with an expired model login.
    lines = [
        'data: {"choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}',
        'data: {"error":{"message":"All models failed (2): anthropic/...","type":"authentication_error"}}',
        "data: [DONE]",
    ]
    with pytest.raises(jv.GatewayError, match="All models failed"):
        list(jv.parse_sse(lines))


# ------------------------------------------------------------------ quiet hours


@pytest.mark.parametrize("now,expected", [
    (dtime(23, 45), True), (dtime(2, 0), True), (dtime(6, 59), True),
    (dtime(7, 0), False), (dtime(18, 0), False), (dtime(23, 29), False),
])
def test_quiet_hours_wrap_past_midnight(now, expected):
    assert jv.in_quiet_hours(now, dtime(23, 30), dtime(7, 0)) is expected


def test_local_answer_handles_time_only():
    assert jv.local_answer("What time is it?").startswith("It's ")
    assert jv.local_answer("Tell me a joke") is None


# ------------------------------------------------------------------ gateway client


class FakeGateway(BaseHTTPRequestHandler):
    seen = {}

    def do_POST(self):  # noqa: N802
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeGateway.seen = {"headers": dict(self.headers), "body": body}
        if self.headers.get("Authorization") != "Bearer test-token":
            self.send_response(401)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        if body["messages"][-1]["content"] == "empty":
            lines = ['data: {"choices":[{"delta":{"role":"assistant"}}]}', "data: [DONE]"]
        else:
            lines = sse("You have college at nine. ", "Leave by 08:25.")
        for line in lines:
            self.wfile.write((line + "\n\n").encode())

    def log_message(self, *args):
        pass


@pytest.fixture
def gateway():
    pytest.importorskip("httpx")
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeGateway)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_stream_reply_sends_session_headers_and_streams(gateway):
    cfg = jv.Config(gateway_url=gateway, gateway_token="test-token")
    text = "".join(jv.stream_reply(cfg, "What's on tomorrow?", threading.Event()))
    assert text == "You have college at nine. Leave by 08:25."
    headers = {k.lower(): v for k, v in FakeGateway.seen["headers"].items()}
    assert headers["x-openclaw-session-key"] == "agent:main:main"
    assert headers["x-openclaw-message-channel"] == "voice"
    assert FakeGateway.seen["body"]["stream"] is True
    assert FakeGateway.seen["body"]["messages"] == [{"role": "user", "content": "What's on tomorrow?"}]


def test_bad_token_raises_gateway_error(gateway):
    cfg = jv.Config(gateway_url=gateway, gateway_token="wrong")
    with pytest.raises(jv.GatewayError):
        list(jv.stream_reply(cfg, "hi", threading.Event()))


def test_gateway_down_falls_back_to_local_answer():
    cfg = jv.Config(gateway_url="http://127.0.0.1:9", gateway_token="x")  # nothing listens on port 9
    assistant = jv.Assistant(cfg, models=None, player=None)
    assert list(assistant.reply_sentences("what time is it", threading.Event()))[0].startswith("It's ")
    fallback = list(assistant.reply_sentences("plan my week", threading.Event()))
    assert "can't reach" in fallback[0]


def test_empty_reply_is_not_silence(gateway):
    cfg = jv.Config(gateway_url=gateway, gateway_token="test-token")
    assistant = jv.Assistant(cfg, models=None, player=None)
    (sentence,) = list(assistant.reply_sentences("empty", threading.Event()))
    assert "can't reach" in sentence


def test_assistant_streams_sentences_from_gateway(gateway):
    cfg = jv.Config(gateway_url=gateway, gateway_token="test-token")
    assistant = jv.Assistant(cfg, models=None, player=None)
    assert list(assistant.reply_sentences("tomorrow?", threading.Event())) == [
        "You have college at nine.", "Leave by 08:25."]


# ------------------------------------------------------------------ config


def test_load_config_reads_example(monkeypatch):
    monkeypatch.setenv("OPENCLAW_GATEWAY_TOKEN", "abc")
    cfg = jv.load_config(str(Path(__file__).resolve().parents[1] / "config.example.toml"))
    assert cfg.input_device == "XVF3800" and cfg.wake_model == "hey_jarvis"
    assert cfg.gateway_token == "abc" and cfg.session_key == "agent:main:main"
    assert cfg.quiet_start == dtime(23, 30) and cfg.server_host == "127.0.0.1"
