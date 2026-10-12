"""Database tables. All datetimes are timezone-aware UTC (see timeutil)."""

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.timeutil import now_utc


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    notes: str = ""
    module_code: str | None = None
    due_at: datetime | None = Field(default=None, index=True)
    priority: int = 2  # 1 = high, 2 = normal, 3 = low
    estimate_mins: int | None = None
    status: str = Field(default="todo", index=True)  # todo / doing / done
    source: str = "manual"  # manual / ai / moodle
    external_uid: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=now_utc)
    completed_at: datetime | None = None


class Reminder(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    task_id: int | None = Field(default=None, foreign_key="task.id", index=True)
    fire_at: datetime = Field(index=True)
    message: str = ""
    auto: bool = False  # generated from a task's due date; regenerated whenever the task changes
    sent_at: datetime | None = None


class ActivityLog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    at: datetime = Field(default_factory=now_utc, index=True)
    actor: str  # ai / dashboard / system
    action: str  # create / update / delete / undo
    entity: str  # task / reminder
    entity_id: int
    summary: str = ""
    before_json: str | None = None
    after_json: str | None = None
    undone_at: datetime | None = None
