from datetime import timedelta

import pytest

from app import scheduler
from app.services import NotFound, reminders, tasks
from app.services.tasks import TaskCreate
from app.timeutil import now_utc


@pytest.fixture
def sent(monkeypatch):
    messages = []
    monkeypatch.setattr("app.notify.send", lambda title, body, **_: messages.append((title, body)) or True)
    return messages


def test_due_reminders_are_sent_once(session, sent):
    reminders.create(session, now_utc() - timedelta(minutes=1), "Email tutor", "ai")
    reminders.create(session, now_utc() + timedelta(hours=1), "Not yet", "ai")
    assert scheduler.send_due_reminders() == 1
    assert sent == [("Reminder", "Email tutor")]
    assert scheduler.send_due_reminders() == 0


def test_auto_reminder_text_uses_current_task_title(session, sent):
    task = tasks.create(session, TaskCreate(title="Stats sheet", due_at=now_utc() + timedelta(hours=3)), "ai")
    pending = reminders.list_pending(session)[0]
    pending.fire_at = now_utc() - timedelta(minutes=1)
    session.add(pending)
    session.commit()
    scheduler.send_due_reminders()
    assert sent[0][0] == "Due soon: Stats sheet"


def test_reminder_for_missing_task_is_rejected(session):
    with pytest.raises(NotFound):
        reminders.create(session, now_utc(), "x", "ai", task_id=42)


def test_digest_lists_overdue_and_upcoming(session):
    tasks.create(session, TaskCreate(title="Late one", due_at=now_utc() - timedelta(hours=1)), "ai")
    tasks.create(session, TaskCreate(title="Next week", due_at=now_utc() + timedelta(days=3)), "ai")
    tasks.create(session, TaskCreate(title="Far away", due_at=now_utc() + timedelta(days=60)), "ai")
    text = scheduler.digest_text()
    assert "Overdue:" in text and "Late one" in text and "Next week" in text
    assert "Far away" not in text


def test_no_digest_when_nothing_due(session):
    assert scheduler.digest_text() is None
