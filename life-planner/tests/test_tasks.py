from datetime import timedelta

import pytest

from app.services import NotFound, reminders, tasks
from app.services.tasks import TaskCreate, TaskUpdate
from tests.conftest import FIXED_NOW


def make(session, title="Essay", hours_from_now=None, actor="dashboard"):
    due = FIXED_NOW + timedelta(hours=hours_from_now) if hours_from_now is not None else None
    return tasks.create(session, TaskCreate(title=title, due_at=due), actor)


def auto_reminder_times(session, task):
    return sorted(r.fire_at for r in reminders.list_pending(session) if r.task_id == task.id and r.auto)


def test_create_adds_reminders_24h_and_2h_before(session, frozen_now):
    task = make(session, hours_from_now=72)
    assert auto_reminder_times(session, task) == [task.due_at - timedelta(hours=24), task.due_at - timedelta(hours=2)]


def test_reminders_in_the_past_are_skipped(session, frozen_now):
    task = make(session, hours_from_now=5)  # 24 h before is already past
    assert auto_reminder_times(session, task) == [task.due_at - timedelta(hours=2)]


def test_ai_tasks_are_marked_as_such(session, frozen_now):
    assert make(session, actor="ai").source == "ai"


def test_changing_due_date_regenerates_reminders(session, frozen_now):
    task = make(session, hours_from_now=72)
    new_due = FIXED_NOW + timedelta(hours=100)
    tasks.update(session, task.id, TaskUpdate(due_at=new_due), "dashboard")
    assert auto_reminder_times(session, task) == [new_due - timedelta(hours=24), new_due - timedelta(hours=2)]


def test_completing_cancels_reminders_and_sets_completed_at(session, frozen_now):
    task = make(session, hours_from_now=72)
    done = tasks.complete(session, task.id, "dashboard")
    assert done.status == "done" and done.completed_at == FIXED_NOW
    assert auto_reminder_times(session, task) == []


def test_clearing_due_date(session, frozen_now):
    task = make(session, hours_from_now=72)
    updated = tasks.update(session, task.id, TaskUpdate(due_at=None), "dashboard")
    assert updated.due_at is None
    assert auto_reminder_times(session, task) == []


def test_list_is_soonest_first_with_undated_last(session, frozen_now):
    make(session, "undated")
    make(session, "later", 50)
    make(session, "sooner", 5)
    assert [t.title for t in tasks.list_tasks(session)] == ["sooner", "later", "undated"]


def test_overview_buckets(session, frozen_now):
    # FIXED_NOW is Mon 13/10 11:00 BST
    make(session, "overdue", -1)
    make(session, "today", 5)  # 16:00 today
    make(session, "this week", 72)
    make(session, "later", 24 * 30)
    make(session, "no date")
    groups = {name: [t.title for t in group] for name, group in tasks.overview(session).items()}
    assert groups == {
        "overdue": ["overdue"],
        "today": ["today"],
        "this_week": ["this week"],
        "later": ["later"],
        "no_date": ["no date"],
    }


def test_missing_task_raises_not_found(session):
    with pytest.raises(NotFound):
        tasks.complete(session, 999, "dashboard")
