"""Time handling.

Rule: inside the app every datetime is timezone-aware UTC (SQLModel stores and returns them that way).
Everything that comes in or goes out (API, MCP, notifications) is ISO-8601 in Europe/London,
so BST/GMT is handled in one place.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_local(value: str | datetime) -> datetime:
    """Parse an ISO-8601 string to aware UTC. A value without an offset is taken as UK local time."""
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LONDON)
    return dt.astimezone(timezone.utc)


def to_local(dt: datetime | None) -> datetime | None:
    return dt.astimezone(LONDON) if dt else None


def iso_local(dt: datetime | None) -> str | None:
    local = to_local(dt)
    return local.isoformat(timespec="minutes") if local else None


def friendly(dt: datetime) -> str:
    """e.g. 'Fri 17 Oct 17:00' for notifications."""
    return to_local(dt).strftime("%a %d %b %H:%M")
