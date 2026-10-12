from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.config import settings
from app.models import Reminder, Task
from app.services import NotFound, activity
from app.timeutil import friendly, now_utc


def delete_for_task(session: Session, task_id: int, auto_only: bool = False) -> None:
    query = select(Reminder).where(Reminder.task_id == task_id, Reminder.sent_at.is_(None))
    if auto_only:
        query = query.where(Reminder.auto.is_(True))
    for reminder in session.exec(query):
        session.delete(reminder)


def sync_auto(session: Session, task: Task) -> None:
    """(Re)generate the automatic 'due soon' reminders for a task. Call after any change to it."""
    delete_for_task(session, task.id, auto_only=True)
    if task.status == "done" or task.due_at is None:
        return
    now = now_utc()
    for hours in settings.reminder_offsets_hours:
        fire_at = task.due_at - timedelta(hours=hours)
        if fire_at > now:
            session.add(Reminder(task_id=task.id, fire_at=fire_at, auto=True))


def create(session: Session, fire_at: datetime, message: str, actor: str, task_id: int | None = None) -> Reminder:
    """A one-off reminder, e.g. "remind me to email my tutor at 3pm"."""
    if task_id is not None and session.get(Task, task_id) is None:
        raise NotFound(f"No task with id {task_id}")
    reminder = Reminder(task_id=task_id, fire_at=fire_at, message=message)
    session.add(reminder)
    session.flush()
    activity.record(session, actor, "create", "reminder", reminder, None, f"Reminder at {friendly(fire_at)}: {message}")
    session.commit()
    session.refresh(reminder)
    return reminder


def due(session: Session) -> list[Reminder]:
    return list(
        session.exec(
            select(Reminder).where(Reminder.sent_at.is_(None), Reminder.fire_at <= now_utc()).order_by(Reminder.fire_at)
        )
    )


def notification_text(session: Session, reminder: Reminder) -> tuple[str, str]:
    """(title, body) for a reminder. Auto reminders are worded from the task at send time so they stay current."""
    task = session.get(Task, reminder.task_id) if reminder.task_id else None
    if task and reminder.auto:
        return f"Due soon: {task.title}", f"Due {friendly(task.due_at)}"
    if task:
        return reminder.message or task.title, task.title
    return "Reminder", reminder.message


def mark_sent(session: Session, reminder: Reminder) -> None:
    reminder.sent_at = now_utc()
    session.add(reminder)
    session.commit()


def list_pending(session: Session) -> list[Reminder]:
    return list(session.exec(select(Reminder).where(Reminder.sent_at.is_(None)).order_by(Reminder.fire_at)))
