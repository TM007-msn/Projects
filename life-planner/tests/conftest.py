import os

# Must be set before the app is imported: in-memory DB, no background jobs, no auth.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SCHEDULER_ENABLED"] = "0"
os.environ.pop("PLANNER_TOKEN", None)
os.environ.pop("NTFY_TOPIC", None)

from datetime import datetime, timezone  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import db  # noqa: E402

# Monday 13/10/2026 10:00 UTC (11:00 BST)
FIXED_NOW = datetime(2026, 10, 13, 10, 0, tzinfo=timezone.utc)


@pytest.fixture
def session():
    db.configure("sqlite://")
    with db.new_session() as s:
        yield s


@pytest.fixture
def frozen_now(monkeypatch):
    """Pin 'now' everywhere the services read it."""
    for module in ("app.services.tasks", "app.services.reminders", "app.services.activity"):
        monkeypatch.setattr(f"{module}.now_utc", lambda: FIXED_NOW)
    return FIXED_NOW


@pytest.fixture
def client():
    from app.main import create_app

    # Host must be localhost: the MCP endpoint rejects unknown Host headers.
    with TestClient(create_app(), base_url="http://localhost") as c:
        yield c


@pytest.fixture
def anyio_backend():
    return "asyncio"
