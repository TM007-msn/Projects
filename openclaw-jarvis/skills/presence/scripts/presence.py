#!/usr/bin/env python3
"""Home/away presence flag for Jarvis.

Set by the iOS Shortcuts "arrive home" / "leave home" automations (through the
Gateway's /hooks/wake endpoint, which tells Jarvis to run this script), and read
by the room-speak skill and the commitment check-ins to decide between speaking
in the room and messaging your phone.

    presence.py set home --source ios-shortcut
    presence.py set away
    presence.py get            # prints {"state": "home", "since": "...", ...}

State: $JARVIS_STATE_DIR/presence.json (default ~/.openclaw/workspace/state).
If the file is missing or older than JARVIS_PRESENCE_MAX_AGE_H hours (default
18), "get" reports "unknown", and callers should treat that as away, because
messaging your phone is the safe fallback.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo(os.environ.get("JARVIS_TZ", "Europe/London"))
MAX_AGE = timedelta(hours=float(os.environ.get("JARVIS_PRESENCE_MAX_AGE_H", "18")))


def path() -> Path:
    default = Path.home() / ".openclaw" / "workspace" / "state"
    return Path(os.environ.get("JARVIS_STATE_DIR", default)).expanduser() / "presence.json"


def get(now: datetime) -> dict:
    p = path()
    if not p.exists():
        return {"state": "unknown", "since": None, "source": None}
    data = json.loads(p.read_text())
    if now - datetime.fromisoformat(data["since"]) > MAX_AGE:
        data = {**data, "state": "unknown", "stale": True}
    return data


def set_state(state: str, source: str, now: datetime) -> dict:
    data = {"state": state, "since": now.isoformat(timespec="seconds"), "source": source}
    p = path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data) + "\n")
    os.replace(tmp, p)
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("set")
    s.add_argument("state", choices=["home", "away"])
    s.add_argument("--source", default="manual")
    sub.add_parser("get")
    args = parser.parse_args(argv)

    now = datetime.now(TZ)
    result = set_state(args.state, args.source, now) if args.cmd == "set" else get(now)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
