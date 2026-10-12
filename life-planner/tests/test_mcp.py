import json

import pytest
from mcp import Client

from app import db
from app.mcp_server import mcp


@pytest.fixture(autouse=True)
def fresh_db():
    db.configure("sqlite://")


def result(call):
    """Tool output as Python data (list returns are structured; dict returns arrive as JSON text)."""
    assert not call.is_error, call.content
    if call.structured_content is not None:
        return call.structured_content["result"]
    return json.loads(call.content[0].text)


@pytest.mark.anyio
async def test_ai_adds_task_and_sees_it_in_overview():
    async with Client(mcp) as client:
        task = result(await client.call_tool("add_task", {"title": "Econ essay", "due_at": "2030-01-10T17:00"}))
        assert task["source"] == "ai" and task["due_at"] == "2030-01-10T17:00+00:00"
        overview = result(await client.call_tool("get_overview", {}))
        assert [t["title"] for t in overview["later"]] == ["Econ essay"]


@pytest.mark.anyio
async def test_ai_changes_are_logged_and_undoable():
    async with Client(mcp) as client:
        task = result(await client.call_tool("add_task", {"title": "Stats sheet"}))
        await client.call_tool("update_task", {"task_id": task["id"], "priority": 1})
        changes = result(await client.call_tool("recent_changes", {}))
        assert changes[0]["actor"] == "ai"
        await client.call_tool("undo", {"change_id": changes[0]["id"]})
        tasks = result(await client.call_tool("list_tasks", {}))
        assert tasks[0]["priority"] == 2


@pytest.mark.anyio
async def test_clear_due_date_and_errors():
    async with Client(mcp) as client:
        task = result(await client.call_tool("add_task", {"title": "x", "due_at": "2030-01-10T17:00"}))
        cleared = result(await client.call_tool("update_task", {"task_id": task["id"], "clear_due_date": True}))
        assert cleared["due_at"] is None
        missing = await client.call_tool("complete_task", {"task_id": 999})
        assert missing.is_error


def test_mcp_endpoint_over_http(client):
    response = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        headers={"Accept": "application/json, text/event-stream"},
    )
    assert response.status_code == 200, response.text


def test_activity_shows_ai_actor_in_dashboard(client):
    # The dashboard and the AI share one database and one log.
    from app.mcp_server import add_task

    add_task("From Claude")
    assert client.get("/api/activity").json()[0]["actor"] == "ai"
