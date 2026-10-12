"""REST API for the dashboard. Thin wrappers around app.services; every change is logged as 'dashboard'."""

from datetime import datetime

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.services import activity, reminders, tasks
from app.services.serialise import reminder_out, task_out
from app.timeutil import parse_local

ACTOR = "dashboard"
router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict:
    return {"ok": True}


@router.get("/overview")
def overview(session: Session = Depends(get_session)) -> dict:
    return {name: [task_out(t) for t in group] for name, group in tasks.overview(session).items()}


@router.get("/tasks")
def list_tasks(status: str = "open", module_code: str | None = None, session: Session = Depends(get_session)) -> list:
    return [task_out(t) for t in tasks.list_tasks(session, status=status, module_code=module_code)]


@router.post("/tasks", status_code=201)
def create_task(data: tasks.TaskCreate, session: Session = Depends(get_session)) -> dict:
    return task_out(tasks.create(session, data, ACTOR))


@router.patch("/tasks/{task_id}")
def update_task(task_id: int, data: tasks.TaskUpdate, session: Session = Depends(get_session)) -> dict:
    return task_out(tasks.update(session, task_id, data, ACTOR))


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, session: Session = Depends(get_session)) -> Response:
    tasks.delete(session, task_id, ACTOR)
    return Response(status_code=204)


class ReminderCreate(BaseModel):
    fire_at: datetime
    message: str
    task_id: int | None = None


@router.get("/reminders")
def list_reminders(session: Session = Depends(get_session)) -> list:
    return [reminder_out(r) for r in reminders.list_pending(session)]


@router.post("/reminders", status_code=201)
def create_reminder(data: ReminderCreate, session: Session = Depends(get_session)) -> dict:
    return reminder_out(reminders.create(session, parse_local(data.fire_at), data.message, ACTOR, data.task_id))


@router.get("/activity")
def recent_activity(limit: int = 20, session: Session = Depends(get_session)) -> list:
    return activity.recent(session, limit)


@router.post("/activity/{change_id}/undo")
def undo(change_id: int, session: Session = Depends(get_session)) -> dict:
    return activity.undo(session, change_id, ACTOR)
