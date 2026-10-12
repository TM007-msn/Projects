from datetime import timedelta

import pytest

from app.models import ActivityLog
from app.services import Conflict, activity, reminders, tasks
from app.services.tasks import TaskCreate, TaskUpdate
from tests.conftest import FIXED_NOW


def change_ids(session):
    return [c["id"] for c in activity.recent(session)]


def test_every_change_is_logged_with_actor(session, frozen_now):
    task = tasks.create(session, TaskCreate(title="Problem sheet"), "ai")
    tasks.complete(session, task.id, "dashboard")
    log = activity.recent(session)
    assert [(c["actor"], c["action"]) for c in log] == [("dashboard", "update"), ("ai", "create")]


def test_undo_create_removes_task_and_its_reminders(session, frozen_now):
    task = tasks.create(session, TaskCreate(title="Essay", due_at=FIXED_NOW + timedelta(days=3)), "ai")
    activity.undo(session, change_ids(session)[0], "dashboard")
    assert tasks.list_tasks(session, status="all") == []
    assert reminders.list_pending(session) == []


def test_undo_delete_restores_task_with_same_id_and_reminders(session, frozen_now):
    task = tasks.create(session, TaskCreate(title="Essay", due_at=FIXED_NOW + timedelta(days=3)), "dashboard")
    tasks.delete(session, task.id, "ai")
    activity.undo(session, change_ids(session)[0], "dashboard")
    restored = tasks.get(session, task.id)
    assert restored.title == "Essay" and restored.due_at == FIXED_NOW + timedelta(days=3)
    assert len(reminders.list_pending(session)) == 2


def test_undo_update_restores_previous_values(session, frozen_now):
    task = tasks.create(session, TaskCreate(title="Essay", priority=2), "dashboard")
    tasks.update(session, task.id, TaskUpdate(title="Econ essay", priority=1), "ai")
    activity.undo(session, change_ids(session)[0], "dashboard")
    task = tasks.get(session, task.id)
    assert (task.title, task.priority) == ("Essay", 2)


def test_cannot_undo_older_change_while_newer_one_stands(session, frozen_now):
    task = tasks.create(session, TaskCreate(title="Essay"), "dashboard")
    tasks.update(session, task.id, TaskUpdate(title="Edited"), "ai")
    newest, oldest = change_ids(session)
    with pytest.raises(Conflict):
        activity.undo(session, oldest, "dashboard")
    activity.undo(session, newest, "dashboard")
    activity.undo(session, oldest, "dashboard")  # allowed now
    assert tasks.list_tasks(session, status="all") == []


def test_cannot_undo_twice(session, frozen_now):
    tasks.create(session, TaskCreate(title="Essay"), "dashboard")
    change_id = change_ids(session)[0]
    activity.undo(session, change_id, "dashboard")
    with pytest.raises(Conflict):
        activity.undo(session, change_id, "dashboard")
    assert session.get(ActivityLog, change_id).undone_at is not None


def test_undo_manual_reminder(session, frozen_now):
    reminders.create(session, FIXED_NOW + timedelta(hours=1), "Email tutor", "ai")
    activity.undo(session, change_ids(session)[0], "dashboard")
    assert reminders.list_pending(session) == []


def test_edit_summary_lists_only_fields_that_changed(session, frozen_now):
    task = tasks.create(session, TaskCreate(title="Essay", priority=2), "dashboard")
    tasks.update(session, task.id, TaskUpdate(title="Essay", priority=1, notes=""), "dashboard")
    assert activity.recent(session)[0]["summary"] == "Edited 'Essay' (priority)"
