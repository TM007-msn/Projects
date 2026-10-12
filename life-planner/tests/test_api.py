from app.config import settings


def test_create_list_complete_via_api(client):
    created = client.post("/api/tasks", json={"title": "Essay", "due_at": "2030-01-10T17:00", "module_code": "EC201"})
    assert created.status_code == 201
    task = created.json()
    assert task["due_at"] == "2030-01-10T17:00+00:00"

    assert [t["title"] for t in client.get("/api/overview").json()["later"]] == ["Essay"]
    assert client.patch(f"/api/tasks/{task['id']}", json={"status": "done"}).json()["status"] == "done"
    assert client.get("/api/tasks").json() == []


def test_validation_and_not_found(client):
    assert client.post("/api/tasks", json={"title": "x", "priority": 5}).status_code == 422
    assert client.post("/api/tasks", json={"title": ""}).status_code == 422
    assert client.patch("/api/tasks/999", json={"title": "y"}).status_code == 404


def test_undo_via_api(client):
    client.post("/api/tasks", json={"title": "Oops"})
    change = client.get("/api/activity").json()[0]
    assert change["can_undo"]
    assert client.post(f"/api/activity/{change['id']}/undo").status_code == 200
    assert client.get("/api/tasks").json() == []
    assert client.post(f"/api/activity/{change['id']}/undo").status_code == 409


def test_token_is_required_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "token", "s3cret")
    assert client.get("/api/tasks").status_code == 401
    assert client.get("/api/tasks", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/api/tasks", headers={"Authorization": "Bearer s3cret"}).status_code == 200
    assert client.get("/api/tasks?token=s3cret").status_code == 200
    assert client.get("/api/health").status_code == 200  # health check stays open
    assert client.get("/").status_code == 200  # dashboard shell holds no data


def test_dashboard_is_served(client):
    assert "<html" in client.get("/").text.lower()
