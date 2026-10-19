#!/usr/bin/env python3
"""Commitment ledger for Jarvis's accountability loop.

Jarvis never edits commitments.json by hand: every change goes through this
script, so the escalation rules (snooze needs a new time, cancel needs a
reason, the ladder stops at "firm") are enforced by code, not by the model
remembering them.

State lives in $JARVIS_STATE_DIR/commitments.json
(default: ~/.openclaw/workspace/state/commitments.json).

Usage examples:
    commitments.py add --what "Maths past paper" --due 20:00 --quote "I'll have it done by 8"
    commitments.py list
    commitments.py due --json              # what needs a nudge right now (read-only)
    commitments.py nudged c3 --stage 2     # record that a nudge was sent
    commitments.py snooze c3 --to 21:00 --reason "dinner ran late"
    commitments.py cancel c3 --reason "teacher moved the deadline"
    commitments.py done c3
    commitments.py summary --date 2026-10-19

Every command accepts --now "YYYY-MM-DD HH:MM" so tests (and you) can
pretend it is a different time.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo(os.environ.get("JARVIS_TZ", "Europe/London"))

# The escalation ladder. Each stage fires at (due time + offset).
# Stage 4 in the spec ("switch channel to the phone") is not a fourth nag:
# it is a delivery rule applied to whichever stage fires while you are away.
LADDER = {
    1: {"name": "friendly", "offset": timedelta(minutes=-30)},
    2: {"name": "reminder", "offset": timedelta(0)},
    3: {"name": "firm", "offset": timedelta(minutes=30)},
}
FINAL_STAGE = max(LADDER)


class LedgerError(Exception):
    """A rule was broken (e.g. cancel without a reason). Shown to the agent."""


# ---------------------------------------------------------------- storage


def state_dir() -> Path:
    default = Path.home() / ".openclaw" / "workspace" / "state"
    return Path(os.environ.get("JARVIS_STATE_DIR", default)).expanduser()


def ledger_path() -> Path:
    return state_dir() / "commitments.json"


@contextlib.contextmanager
def locked_ledger():
    """Load the ledger under an exclusive lock and save it atomically on exit.

    The lock stops the watcher automation and a chat turn from writing at the
    same moment. Writing to a temp file then os.replace() means a crash can
    never leave a half-written JSON file behind.
    """
    path = ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path.with_suffix(".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = load(path)
        yield data
        fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".commitments-")
        with os.fdopen(fd, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)


def load(path: Path | None = None) -> dict:
    path = path or ledger_path()
    if not path.exists():
        return {"version": 1, "next_id": 1, "commitments": []}
    with open(path) as f:
        return json.load(f)


def find(data: dict, cid: str) -> dict:
    for c in data["commitments"]:
        if c["id"] == cid:
            return c
    raise LedgerError(f"No commitment with id {cid!r}. Run `list` to see ids.")


def require_open(c: dict) -> None:
    if c["state"] != "open":
        raise LedgerError(f"{c['id']} is already {c['state']}.")


# ---------------------------------------------------------------- time


def parse_now(value: str | None) -> datetime:
    if value:
        return parse_time(value, reference=datetime.now(TZ), roll_forward=False)
    return datetime.now(TZ)


def parse_time(value: str, reference: datetime, roll_forward: bool = True) -> datetime:
    """Turn "20:00", "2026-10-19 20:00" or a full ISO string into an aware datetime.

    A bare "HH:MM" means today; if that time has already passed (by more than a
    minute) it means tomorrow, so "by 01:00" said at 23:00 does the right thing.
    """
    value = value.strip()
    try:
        t = datetime.strptime(value, "%H:%M").time()
    except ValueError:
        pass
    else:
        result = datetime.combine(reference.date(), t, tzinfo=TZ)
        if roll_forward and result < reference - timedelta(minutes=1):
            result += timedelta(days=1)
        return result

    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=TZ)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise LedgerError(
            f"Can't read the time {value!r}. Use HH:MM or YYYY-MM-DD HH:MM."
        ) from None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=TZ)


def iso(dt: datetime) -> str:
    return dt.astimezone(TZ).isoformat(timespec="minutes")


def from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(TZ)


def stage_time(c: dict, stage: int) -> datetime:
    return from_iso(c["due"]) + LADDER[stage]["offset"]


# ---------------------------------------------------------------- commands


def cmd_add(data: dict, args, now: datetime) -> dict:
    due = parse_time(args.due, reference=now)
    if due <= now:
        raise LedgerError("The due time is in the past. Ask for a new time.")
    cid = f"c{data['next_id']}"
    data["next_id"] += 1
    c = {
        "id": cid,
        "what": args.what,
        "quote": args.quote or "",
        "due": iso(due),
        "created": iso(now),
        "state": "open",
        "stage": 0,
        "nudges": [],
        "snoozes": [],
        "cancel_reason": None,
        "closed_at": None,
    }
    data["commitments"].append(c)
    return c


def cmd_done(data: dict, args, now: datetime) -> dict:
    c = find(data, args.id)
    require_open(c)
    c["state"] = "done"
    c["closed_at"] = iso(now)
    return c


def cmd_snooze(data: dict, args, now: datetime) -> dict:
    c = find(data, args.id)
    require_open(c)
    new_due = parse_time(args.to, reference=now)
    if new_due <= now:
        raise LedgerError("A snooze needs a new time in the future.")
    c["snoozes"].append(
        {"at": iso(now), "from": c["due"], "to": iso(new_due), "reason": args.reason}
    )
    c["due"] = iso(new_due)
    c["stage"] = 0  # the ladder starts again from the new time
    return c


def cmd_cancel(data: dict, args, now: datetime) -> dict:
    if not args.reason or not args.reason.strip():
        raise LedgerError("Cancelling needs a reason; it is raised in the evening review.")
    c = find(data, args.id)
    require_open(c)
    c["state"] = "cancelled"
    c["cancel_reason"] = args.reason.strip()
    c["closed_at"] = iso(now)
    return c


def cmd_nudged(data: dict, args, now: datetime) -> dict:
    c = find(data, args.id)
    require_open(c)
    if args.stage not in LADDER:
        raise LedgerError(f"Stage must be one of {sorted(LADDER)}.")
    if args.stage <= c["stage"]:
        raise LedgerError(f"Stage {args.stage} was already sent for {c['id']}.")
    c["stage"] = args.stage
    c["nudges"].append({"at": iso(now), "stage": args.stage, "channel": args.channel})
    return c


def due_nudges(data: dict, now: datetime) -> list[dict]:
    """Which open commitments need a nudge now, and at which stage.

    If several stages are overdue (e.g. the gateway was off), only the highest
    one is returned: you get one firm message, not three in a row. Nothing is
    returned once the final stage has been sent: the ladder stops at firm.
    """
    result = []
    for c in data["commitments"]:
        if c["state"] != "open" or c["stage"] >= FINAL_STAGE:
            continue
        reached = [s for s in LADDER if s > c["stage"] and stage_time(c, s) <= now]
        if not reached:
            continue
        stage = max(reached)
        result.append(
            {
                "id": c["id"],
                "what": c["what"],
                "quote": c["quote"],
                "due": c["due"],
                "stage": stage,
                "stage_name": LADDER[stage]["name"],
                "snooze_count": len(c["snoozes"]),
                "minutes_past_due": int((now - from_iso(c["due"])).total_seconds() // 60),
            }
        )
    return result


def day_summary(data: dict, day: date) -> dict:
    """Everything that matters for the evening review of one day."""

    def on_day(value: str | None) -> bool:
        return bool(value) and from_iso(value).date() == day

    out = {"date": day.isoformat(), "done": [], "cancelled": [], "snoozed": [], "open": []}
    for c in data["commitments"]:
        if c["state"] == "done" and on_day(c["closed_at"]):
            out["done"].append(c)
        elif c["state"] == "cancelled" and on_day(c["closed_at"]):
            out["cancelled"].append(c)
        elif c["state"] == "open":
            out["open"].append(c)
        if any(on_day(s["at"]) for s in c["snoozes"]):
            out["snoozed"].append(c)
    return out


# ---------------------------------------------------------------- output


def describe(c: dict) -> str:
    due = from_iso(c["due"]).strftime("%a %d/%m %H:%M")
    line = f"{c['id']}  [{c['state']}]  {c['what']}  (due {due}, stage {c['stage']})"
    if c["snoozes"]:
        line += f"  snoozed x{len(c['snoozes'])}"
    if c["cancel_reason"]:
        line += f"  reason: {c['cancel_reason']}"
    return line


def emit(obj, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, indent=2))
    elif isinstance(obj, list):
        print("\n".join(describe(c) for c in obj) if obj else "Nothing.")
    elif isinstance(obj, dict) and "id" in obj:
        print(describe(obj))
    else:
        print(json.dumps(obj, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--now", help="pretend the current time is this (testing)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="record a new commitment")
    a.add_argument("--what", required=True)
    a.add_argument("--due", required=True, help="HH:MM or YYYY-MM-DD HH:MM")
    a.add_argument("--quote", help="your own words, quoted back in reminders")

    ls = sub.add_parser("list", help="show commitments")
    ls.add_argument("--all", action="store_true", help="include done and cancelled")

    d = sub.add_parser("done", help="mark a commitment complete")
    d.add_argument("id")

    s = sub.add_parser("snooze", help="move the due time (new time required)")
    s.add_argument("id")
    s.add_argument("--to", required=True)
    s.add_argument("--reason")

    c = sub.add_parser("cancel", help="drop a commitment (reason required)")
    c.add_argument("id")
    c.add_argument("--reason", required=True)

    n = sub.add_parser("nudged", help="record that a ladder stage was sent")
    n.add_argument("id")
    n.add_argument("--stage", type=int, required=True)
    n.add_argument("--channel", default="telegram", help="voice | telegram | ios")

    sub.add_parser("due", help="list nudges that are due now (read-only)")

    sm = sub.add_parser("summary", help="evening-review summary for one day")
    sm.add_argument("--date", help="YYYY-MM-DD (default: today)")
    return p


WRITERS = {
    "add": cmd_add,
    "done": cmd_done,
    "snooze": cmd_snooze,
    "cancel": cmd_cancel,
    "nudged": cmd_nudged,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        now = parse_now(args.now)
        if args.cmd in WRITERS:
            with locked_ledger() as data:
                result = WRITERS[args.cmd](data, args, now)
            emit(result, args.json)
        elif args.cmd == "list":
            items = load()["commitments"]
            if not args.all:
                items = [c for c in items if c["state"] == "open"]
            emit(items, args.json)
        elif args.cmd == "due":
            emit(due_nudges(load(), now), True)
        elif args.cmd == "summary":
            day = date.fromisoformat(args.date) if args.date else now.date()
            emit(day_summary(load(), day), True)
    except LedgerError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
