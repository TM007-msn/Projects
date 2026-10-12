"""Converting rows to/from JSON: raw UTC snapshots for the activity log, UK-local dicts for clients."""

import json
from datetime import datetime

from sqlmodel import SQLModel

from app.models import Reminder, Task
from app.timeutil import iso_local


def snapshot(row: SQLModel) -> str:
    """Exact copy of a row (UTC datetimes with offset) so undo can restore it."""
    return row.model_dump_json()


def restore(model: type[SQLModel], raw: str) -> SQLModel:
    data = json.loads(raw)
    # Table models skip validation, so turn ISO strings back into datetimes by hand.
    for name, info in model.model_fields.items():
        if data.get(name) and "datetime" in str(info.annotation):
            data[name] = datetime.fromisoformat(data[name])
    return model(**data)


def task_out(task: Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "notes": task.notes,
        "module_code": task.module_code,
        "due_at": iso_local(task.due_at),
        "priority": task.priority,
        "estimate_mins": task.estimate_mins,
        "status": task.status,
        "source": task.source,
        "created_at": iso_local(task.created_at),
        "completed_at": iso_local(task.completed_at),
    }


def reminder_out(reminder: Reminder) -> dict:
    return {
        "id": reminder.id,
        "task_id": reminder.task_id,
        "fire_at": iso_local(reminder.fire_at),
        "message": reminder.message,
        "auto": reminder.auto,
        "sent_at": iso_local(reminder.sent_at),
    }
