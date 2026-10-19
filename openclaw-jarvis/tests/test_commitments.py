"""Tests for skills/commitments/scripts/commitments.py.

Run from the repo folder:  python3 -m pytest tests/
"""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/commitments/scripts/commitments.py"
spec = importlib.util.spec_from_file_location("commitments", SCRIPT)
commitments = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commitments)


@pytest.fixture(autouse=True)
def state_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_STATE_DIR", str(tmp_path))
    return tmp_path


def run(*argv):
    return commitments.main(list(argv))


def ledger():
    return commitments.load()["commitments"]


def due_at(now, capsys):
    capsys.readouterr()
    assert run("--now", now, "due") == 0
    return json.loads(capsys.readouterr().out)


def add_maths():
    assert run("--now", "2026-10-19 18:00", "add", "--what", "Maths past paper",
               "--due", "20:00", "--quote", "I'll have it done by 8") == 0


def test_add_uses_today_and_records_quote():
    add_maths()
    (c,) = ledger()
    assert c["due"].startswith("2026-10-19T20:00")
    assert c["quote"] == "I'll have it done by 8"
    assert c["state"] == "open" and c["stage"] == 0


def test_bare_time_already_passed_rolls_to_tomorrow():
    assert run("--now", "2026-10-19 23:00", "add", "--what", "Read notes", "--due", "01:00") == 0
    assert ledger()[0]["due"].startswith("2026-10-20T01:00")


def test_ladder_stages_fire_in_order_and_stop_at_firm(capsys):
    add_maths()
    assert due_at("2026-10-19 19:00", capsys) == []
    (n,) = due_at("2026-10-19 19:30", capsys)
    assert n["stage"] == 1 and n["stage_name"] == "friendly"
    run("--now", "2026-10-19 19:31", "nudged", "c1", "--stage", "1")
    assert due_at("2026-10-19 19:45", capsys) == []
    (n,) = due_at("2026-10-19 20:00", capsys)
    assert n["stage_name"] == "reminder" and n["quote"] == "I'll have it done by 8"
    run("--now", "2026-10-19 20:01", "nudged", "c1", "--stage", "2")
    (n,) = due_at("2026-10-19 20:30", capsys)
    assert n["stage_name"] == "firm" and n["minutes_past_due"] == 30
    run("--now", "2026-10-19 20:31", "nudged", "c1", "--stage", "3")
    # The ladder stops at firm: no more nagging, however late it gets.
    assert due_at("2026-10-19 23:59", capsys) == []


def test_missed_stages_collapse_into_the_highest(capsys):
    add_maths()
    (n,) = due_at("2026-10-19 21:00", capsys)
    assert n["stage"] == 3


def test_snooze_requires_future_time_and_restarts_ladder(capsys):
    add_maths()
    run("--now", "2026-10-19 20:01", "nudged", "c1", "--stage", "2")
    assert run("--now", "2026-10-19 20:05", "snooze", "c1", "--to", "2026-10-19 19:00") == 2
    assert run("--now", "2026-10-19 20:05", "snooze", "c1", "--to", "21:00",
               "--reason", "dinner ran late") == 0
    (c,) = ledger()
    assert c["stage"] == 0 and c["due"].startswith("2026-10-19T21:00")
    assert c["snoozes"][0]["reason"] == "dinner ran late"
    (n,) = due_at("2026-10-19 20:30", capsys)
    assert n["stage"] == 1 and n["snooze_count"] == 1


def test_snooze_without_new_time_is_rejected():
    add_maths()
    with pytest.raises(SystemExit):  # argparse: --to is required
        run("snooze", "c1")


def test_cancel_requires_a_reason():
    add_maths()
    assert run("--now", "2026-10-19 19:00", "cancel", "c1", "--reason", "   ") == 2
    assert ledger()[0]["state"] == "open"
    assert run("--now", "2026-10-19 19:00", "cancel", "c1", "--reason", "deadline moved") == 0
    assert ledger()[0]["cancel_reason"] == "deadline moved"


def test_closed_commitments_get_no_nudges_and_cannot_change(capsys):
    add_maths()
    run("--now", "2026-10-19 19:00", "done", "c1")
    assert due_at("2026-10-19 21:00", capsys) == []
    assert run("--now", "2026-10-19 19:05", "snooze", "c1", "--to", "21:00") == 2


def test_cannot_resend_same_stage():
    add_maths()
    assert run("nudged", "c1", "--stage", "1") == 0
    assert run("nudged", "c1", "--stage", "1") == 2


def test_summary_groups_the_day(capsys):
    add_maths()
    run("--now", "2026-10-19 18:05", "add", "--what", "Econ essay plan", "--due", "21:00")
    run("--now", "2026-10-19 18:10", "add", "--what", "CS NEA write-up", "--due", "22:00")
    run("--now", "2026-10-19 19:50", "done", "c1")
    run("--now", "2026-10-19 20:00", "snooze", "c2", "--to", "2026-10-20 17:00")
    run("--now", "2026-10-19 20:10", "cancel", "c3", "--reason", "teacher extended it")
    capsys.readouterr()
    run("--now", "2026-10-19 22:00", "summary")
    s = json.loads(capsys.readouterr().out)
    assert [c["id"] for c in s["done"]] == ["c1"]
    assert [c["id"] for c in s["cancelled"]] == ["c3"]
    assert [c["id"] for c in s["snoozed"]] == ["c2"]
    assert [c["id"] for c in s["open"]] == ["c2"]
