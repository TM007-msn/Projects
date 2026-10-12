"""Settings read from environment variables (see .env.example)."""

import os
from dataclasses import dataclass, field


def _list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


@dataclass
class Settings:
    database_url: str = field(default_factory=lambda: os.environ.get("DATABASE_URL", "sqlite:///./data/planner.db"))
    # Shared secret for /api and /mcp. Leave unset only when running on localhost.
    token: str | None = field(default_factory=lambda: os.environ.get("PLANNER_TOKEN") or None)
    # Public hostnames the MCP endpoint may be reached on (e.g. planner.example.com behind a tunnel).
    public_hosts: list[str] = field(default_factory=lambda: _list("PUBLIC_HOSTS"))
    ntfy_url: str = field(default_factory=lambda: os.environ.get("NTFY_URL", "https://ntfy.sh").rstrip("/"))
    ntfy_topic: str | None = field(default_factory=lambda: os.environ.get("NTFY_TOPIC") or None)
    digest_time: str = field(default_factory=lambda: os.environ.get("DIGEST_TIME", "08:00"))
    reminder_offsets_hours: list[float] = field(
        default_factory=lambda: [float(h) for h in _list("REMINDER_OFFSETS_HOURS", "24,2")]
    )
    scheduler_enabled: bool = field(default_factory=lambda: os.environ.get("SCHEDULER_ENABLED", "1") == "1")


settings = Settings()
