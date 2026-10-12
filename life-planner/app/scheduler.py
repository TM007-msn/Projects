"""Background jobs: due reminders every minute and a morning digest."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app import db, notify
from app.config import settings
from app.services import reminders, tasks
from app.timeutil import LONDON, friendly

log = logging.getLogger(__name__)


def send_due_reminders() -> int:
    sent = 0
    with db.new_session() as session:
        for reminder in reminders.due(session):
            title, body = reminders.notification_text(session, reminder)
            # Mark as sent even if ntfy is down, so one outage doesn't cause a flood later.
            notify.send(title, body, priority="high" if reminder.auto else "default", tags="alarm_clock")
            reminders.mark_sent(session, reminder)
            sent += 1
    return sent


def digest_text() -> str | None:
    with db.new_session() as session:
        buckets = tasks.overview(session)
    lines = []
    for key, label in (("overdue", "Overdue"), ("today", "Today"), ("this_week", "Next 7 days")):
        if buckets[key]:
            lines.append(f"{label}:")
            lines += [f"  • {t.title} ({friendly(t.due_at)})" for t in buckets[key]]
    return "\n".join(lines) or None


def send_digest() -> None:
    text = digest_text()
    if text:
        notify.send("Your day", text, tags="sunrise")


def start() -> AsyncIOScheduler:
    hour, minute = (int(part) for part in settings.digest_time.split(":"))
    scheduler = AsyncIOScheduler(timezone=LONDON)
    scheduler.add_job(send_due_reminders, "interval", minutes=1, id="reminders")
    scheduler.add_job(send_digest, CronTrigger(hour=hour, minute=minute, timezone=LONDON), id="digest")
    scheduler.start()
    log.info("Scheduler started (digest at %s)", settings.digest_time)
    return scheduler
