"""Activity log: every change records who made it and a before/after snapshot, so any change can be undone."""

from sqlmodel import Session, select

from app.models import ActivityLog, Reminder, Task
from app.services import Conflict, NotFound
from app.services.serialise import restore, snapshot
from app.timeutil import iso_local, now_utc

ENTITIES = {"task": Task, "reminder": Reminder}


def record(session: Session, actor: str, action: str, entity: str, row, before: str | None, summary: str) -> None:
    after = None if action == "delete" else snapshot(row)
    session.add(
        ActivityLog(
            actor=actor,
            action=action,
            entity=entity,
            entity_id=row.id,
            summary=summary,
            before_json=before,
            after_json=after,
        )
    )


def recent(session: Session, limit: int = 20) -> list[dict]:
    rows = session.exec(select(ActivityLog).order_by(ActivityLog.id.desc()).limit(limit)).all()
    return [
        {
            "id": r.id,
            "at": iso_local(r.at),
            "actor": r.actor,
            "action": r.action,
            "entity": r.entity,
            "entity_id": r.entity_id,
            "summary": r.summary,
            "undone": r.undone_at is not None,
            "can_undo": r.action != "undo" and r.undone_at is None,
        }
        for r in rows
    ]


def undo(session: Session, change_id: int, actor: str) -> dict:
    change = session.get(ActivityLog, change_id)
    if change is None:
        raise NotFound(f"No change with id {change_id}")
    if change.action == "undo" or change.undone_at is not None:
        raise Conflict("That change can't be undone (already undone, or it is itself an undo)")

    later = session.exec(
        select(ActivityLog).where(
            ActivityLog.entity == change.entity,
            ActivityLog.entity_id == change.entity_id,
            ActivityLog.id > change.id,
            ActivityLog.action != "undo",
            ActivityLog.undone_at.is_(None),
        )
    ).first()
    if later is not None:
        raise Conflict(f"Change {later.id} edited the same {change.entity} afterwards; undo that one first")

    from app.services import reminders as reminder_service  # local import: reminders imports this module

    model = ENTITIES[change.entity]
    current = session.get(model, change.entity_id)
    if change.action == "create":
        if current is not None:
            if change.entity == "task":
                reminder_service.delete_for_task(session, current.id)
            session.delete(current)
    else:  # update or delete: put the "before" snapshot back
        restored = restore(model, change.before_json)
        if current is not None:
            for name in model.model_fields:
                setattr(current, name, getattr(restored, name))
            restored = current
        session.add(restored)
        session.flush()
        if change.entity == "task":
            reminder_service.sync_auto(session, restored)

    change.undone_at = now_utc()
    session.add(change)
    session.add(
        ActivityLog(
            actor=actor,
            action="undo",
            entity=change.entity,
            entity_id=change.entity_id,
            summary=f"Undid: {change.summary}",
        )
    )
    session.commit()
    return {"undone": change.id, "summary": change.summary}
