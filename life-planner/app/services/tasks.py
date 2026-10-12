from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.models import Task
from app.services import NotFound
from app.services import activity
from app.services import reminders as reminder_service
from app.services.serialise import snapshot
from app.timeutil import now_utc, parse_local, to_local

FAR_FUTURE = datetime.max.replace(tzinfo=timezone.utc)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    notes: str = ""
    module_code: str | None = None
    due_at: datetime | None = None  # UK local if no offset given
    priority: int = Field(default=2, ge=1, le=3)
    estimate_mins: int | None = Field(default=None, ge=0)


class TaskUpdate(BaseModel):
    """Only the fields that are sent get changed. Send due_at: null to clear the due date."""

    title: str | None = Field(default=None, min_length=1)
    notes: str | None = None
    module_code: str | None = None
    due_at: datetime | None = None
    priority: int | None = Field(default=None, ge=1, le=3)
    estimate_mins: int | None = Field(default=None, ge=0)
    status: str | None = Field(default=None, pattern="^(todo|doing|done)$")


def get(session: Session, task_id: int) -> Task:
    task = session.get(Task, task_id)
    if task is None:
        raise NotFound(f"No task with id {task_id}")
    return task


def list_tasks(
    session: Session, status: str = "open", module_code: str | None = None, due_within_days: int | None = None
) -> list[Task]:
    query = select(Task)
    if status == "open":
        query = query.where(Task.status != "done")
    elif status == "done":
        query = query.where(Task.status == "done")
    if module_code:
        query = query.where(Task.module_code == module_code)
    if due_within_days is not None:
        query = query.where(Task.due_at.is_not(None), Task.due_at <= now_utc() + timedelta(days=due_within_days))
    tasks = session.exec(query).all()
    # Dated tasks first (soonest first), then undated; priority breaks ties.
    return sorted(tasks, key=lambda t: (t.due_at is None, t.due_at or FAR_FUTURE, t.priority))


def create(session: Session, data: TaskCreate, actor: str) -> Task:
    values = data.model_dump()
    if data.due_at is not None:
        values["due_at"] = parse_local(data.due_at)
    task = Task(**values, source="ai" if actor == "ai" else "manual")
    session.add(task)
    session.flush()
    reminder_service.sync_auto(session, task)
    activity.record(session, actor, "create", "task", task, None, f"Added task '{task.title}'")
    session.commit()
    session.refresh(task)
    return task


def update(session: Session, task_id: int, data: TaskUpdate, actor: str) -> Task:
    task = get(session, task_id)
    before = snapshot(task)
    changes = data.model_dump(exclude_unset=True)
    if changes.get("due_at") is not None:
        changes["due_at"] = parse_local(changes["due_at"])
    if "status" in changes:
        changes["completed_at"] = now_utc() if changes["status"] == "done" else None
    # Only count fields whose value really changes (the dashboard sends the whole form).
    changed = [name for name, value in changes.items() if getattr(task, name) != value]
    for name in changed:
        setattr(task, name, changes[name])
    session.add(task)
    reminder_service.sync_auto(session, task)
    if changes.get("status") == "done":
        summary = f"Completed '{task.title}'"
    else:
        fields = ", ".join(name.replace("_", " ") for name in changed if name != "completed_at")
        summary = f"Edited '{task.title}' ({fields or 'no changes'})"
    activity.record(session, actor, "update", "task", task, before, summary)
    session.commit()
    session.refresh(task)
    return task


def complete(session: Session, task_id: int, actor: str) -> Task:
    return update(session, task_id, TaskUpdate(status="done"), actor)


def delete(session: Session, task_id: int, actor: str) -> None:
    task = get(session, task_id)
    before = snapshot(task)
    reminder_service.delete_for_task(session, task.id)
    activity.record(session, actor, "delete", "task", task, before, f"Deleted task '{task.title}'")
    session.delete(task)
    session.commit()


def overview(session: Session) -> dict[str, list[Task]]:
    """Open tasks grouped the way the dashboard shows them, using UK calendar days."""
    now_local = to_local(now_utc())
    end_of_today = now_local.replace(hour=23, minute=59, second=59, microsecond=0)
    end_of_week = end_of_today + timedelta(days=7)
    buckets: dict[str, list[Task]] = {"overdue": [], "today": [], "this_week": [], "later": [], "no_date": []}
    for task in list_tasks(session, status="open"):
        due = to_local(task.due_at)
        if due is None:
            buckets["no_date"].append(task)
        elif due < now_local:
            buckets["overdue"].append(task)
        elif due <= end_of_today:
            buckets["today"].append(task)
        elif due <= end_of_week:
            buckets["this_week"].append(task)
        else:
            buckets["later"].append(task)
    return buckets

