import uuid


def ev(**over):
    e = {"id": str(uuid.uuid4()), "ts": "2026-11-02T08:00:00+00:00",
         "type": "rating", "target": "1.1.1a", "data": {"value": "got"}}
    e.update(over)
    return e


def test_insert_and_list(logged_in):
    e = ev()
    r = logged_in.post("/api/events", json={"events": [e]})
    assert r.json() == {"accepted": 1, "duplicates": 0}
    got = logged_in.get("/api/events").json()["events"]
    assert len(got) == 1 and got[0]["id"] == e["id"] and got[0]["data"] == {"value": "got"}


def test_resending_same_event_is_ignored(logged_in):
    e = ev()
    logged_in.post("/api/events", json={"events": [e]})
    r = logged_in.post("/api/events", json={"events": [e, e]})
    assert r.json() == {"accepted": 0, "duplicates": 2}
    assert len(logged_in.get("/api/events").json()["events"]) == 1


def test_mixed_batch_counts_duplicates(logged_in):
    a, b = ev(), ev()
    logged_in.post("/api/events", json={"events": [a]})
    assert logged_in.post("/api/events", json={"events": [a, b]}).json() == {"accepted": 1, "duplicates": 1}


def test_uppercase_uuid_is_normalised_so_duplicates_still_match(logged_in):
    e = ev()
    logged_in.post("/api/events", json={"events": [e]})
    upper = dict(e, id=e["id"].upper())
    assert logged_in.post("/api/events", json={"events": [upper]}).json()["duplicates"] == 1


def test_validation(logged_in):
    bad = [
        ev(id="not-a-uuid"),
        ev(ts="2026-11-02T08:00:00"),            # no timezone
        ev(ts="yesterday"),
        ev(type="delete_everything"),
        ev(data={"value": "maybe"}),             # bad rating value
        ev(target="1.1.1a; DROP TABLE events"),
        ev(type="flag", data={"note": 5}),
        ev(type="flag", data={"note": "x" * 3000}),
    ]
    for e in bad:
        r = logged_in.post("/api/events", json={"events": [e]})
        assert r.status_code == 422, e
    assert logged_in.get("/api/events").json()["events"] == []


def test_flag_and_verify_events_accepted(logged_in):
    batch = [ev(type="flag", target="kw-mar", data={"note": "Should mention 'currently'"}),
             ev(type="verify", target="kw-mdr", data={}),
             ev(type="unflag", target="kw-mar", data={})]
    assert logged_in.post("/api/events", json={"events": batch}).json()["accepted"] == 3


def test_events_survive_app_restart(settings, client):
    from fastapi.testclient import TestClient
    from app.main import create_app
    from tests.conftest import PASSWORD
    client.post("/api/login", json={"password": PASSWORD})
    client.post("/api/events", json={"events": [ev()]})
    again = TestClient(create_app(settings))
    again.post("/api/login", json={"password": PASSWORD})
    assert len(again.get("/api/events").json()["events"]) == 1
