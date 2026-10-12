"""MCP server: the tools the AI agent (e.g. the Claude app) uses. Thin wrappers around app.services, logged as 'ai'."""

from typing import Annotated, Literal

from pydantic import Field

from mcp.server.mcpserver import MCPServer
from app import db
from app.services import activity, reminders, tasks
from app.services.serialise import reminder_out, task_out
from app.timeutil import iso_local, now_utc, parse_local

ACTOR = "ai"
DateTimeStr = Annotated[
    str,
    Field(description="ISO-8601 date-time, e.g. '2026-10-17T17:00'. Without an offset it is read as UK time."),
]

mcp = MCPServer(
    "student-life-planner",
    instructions=(
        "Personal planner for a UK university student. Times are Europe/London. "
        "Call get_overview first to see what is open before planning. "
        "If the user gives a day without a time for a deadline, assume 17:00. "
        "After changing anything, briefly confirm what changed; every change can be reverted with undo."
    ),
)


@mcp.tool()
def get_overview() -> dict:
    """Current time plus open tasks grouped into overdue / today / this_week / later / no_date."""
    with db.new_session() as session:
        groups = {name: [task_out(t) for t in group] for name, group in tasks.overview(session).items()}
    return {"now": iso_local(now_utc()), **groups}


@mcp.tool()
def list_tasks(
    status: Literal["open", "done", "all"] = "open",
    module_code: str | None = None,
    due_within_days: Annotated[int | None, Field(description="Only tasks due within this many days")] = None,
) -> list[dict]:
    """List tasks, soonest due first."""
    with db.new_session() as session:
        return [task_out(t) for t in tasks.list_tasks(session, status, module_code, due_within_days)]


@mcp.tool()
def add_task(
    title: str,
    due_at: DateTimeStr | None = None,
    notes: str = "",
    module_code: Annotated[str | None, Field(description="Uni module code, e.g. 'EC201'")] = None,
    priority: Annotated[int, Field(ge=1, le=3, description="1 high, 2 normal, 3 low")] = 2,
    estimate_mins: Annotated[int | None, Field(description="Rough effort estimate in minutes")] = None,
) -> dict:
    """Add a task or deadline. Reminders 24 h and 2 h before the due time are created automatically."""
    data = tasks.TaskCreate(
        title=title, due_at=due_at, notes=notes, module_code=module_code, priority=priority, estimate_mins=estimate_mins
    )
    with db.new_session() as session:
        return task_out(tasks.create(session, data, ACTOR))


@mcp.tool()
def update_task(
    task_id: int,
    title: str | None = None,
    due_at: DateTimeStr | None = None,
    clear_due_date: bool = False,
    notes: str | None = None,
    module_code: str | None = None,
    priority: Annotated[int | None, Field(ge=1, le=3)] = None,
    estimate_mins: int | None = None,
    status: Literal["todo", "doing", "done"] | None = None,
) -> dict:
    """Change some fields of a task. Fields left out are not changed."""
    changes = {
        name: value
        for name, value in dict(
            title=title, due_at=due_at, notes=notes, module_code=module_code,
            priority=priority, estimate_mins=estimate_mins, status=status,
        ).items()
        if value is not None
    }
    if clear_due_date:
        changes["due_at"] = None
    with db.new_session() as session:
        return task_out(tasks.update(session, task_id, tasks.TaskUpdate(**changes), ACTOR))


@mcp.tool()
def complete_task(task_id: int) -> dict:
    """Mark a task as done (its pending reminders are cancelled)."""
    with db.new_session() as session:
        return task_out(tasks.complete(session, task_id, ACTOR))


@mcp.tool()
def delete_task(task_id: int) -> str:
    """Delete a task. Prefer complete_task for finished work; use this for tasks added by mistake."""
    with db.new_session() as session:
        tasks.delete(session, task_id, ACTOR)
    return f"Deleted task {task_id}"


@mcp.tool()
def set_reminder(
    at: DateTimeStr,
    message: str,
    task_id: Annotated[int | None, Field(description="Optionally link the reminder to a task")] = None,
) -> dict:
    """Send a push notification to the user's phone at a given time."""
    with db.new_session() as session:
        return reminder_out(reminders.create(session, parse_local(at), message, ACTOR, task_id))


@mcp.tool()
def recent_changes(limit: int = 20) -> list[dict]:
    """Recent changes made by the AI, the dashboard or the system, newest first. Use the id with undo."""
    with db.new_session() as session:
        return activity.recent(session, limit)


@mcp.tool()
def undo(change_id: int) -> dict:
    """Revert one change from recent_changes."""
    with db.new_session() as session:
        return activity.undo(session, change_id, ACTOR)
