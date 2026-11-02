import time

from app import auth
from tests.conftest import PASSWORD


def test_password_hash_round_trip():
    h = auth.hash_password("hunter2hunter2")
    assert h.startswith("scrypt:") and "$" not in h  # no '$': Docker Compose would mangle it
    assert auth.verify_password("hunter2hunter2", h)
    assert not auth.verify_password("hunter2hunter3", h)


def test_verify_password_rejects_garbage_hash():
    assert not auth.verify_password("anything", "not-a-hash")
    assert not auth.verify_password("anything", "bcrypt:1:2:3:abc:def")


def test_session_token_signature_and_expiry():
    key = "k" * 40
    token = auth.make_session_token(key, days=1, now=1000)
    assert auth.check_session_token(token, key, now=1000)
    assert not auth.check_session_token(token, key, now=1000 + 86400 + 1)   # expired
    assert not auth.check_session_token(token, "other" * 10, now=1000)      # wrong key
    expiry, sig = token.split(".")
    forged = f"{int(expiry) + 999999}.{sig}"                                 # extended expiry
    assert not auth.check_session_token(forged, key, now=1000)
    assert not auth.check_session_token(None, key)
    assert not auth.check_session_token("nodot", key)


def test_rate_limiter_blocks_after_five_failures():
    rl = auth.LoginRateLimiter(limit=5, window=900)
    for i in range(5):
        assert not rl.blocked("ip", now=100 + i)
        rl.record_failure("ip", now=100 + i)
    assert rl.blocked("ip", now=110)
    assert not rl.blocked("ip", now=100 + 4 + 901)  # window has passed


def test_protected_routes_need_login(client):
    for method, path in [("get", "/api/events"), ("get", "/content/spec.json")]:
        assert getattr(client, method)(path).status_code == 401
    r = client.post("/api/events", json={"events": []})
    assert r.status_code == 401


def test_public_routes(client):
    assert client.get("/api/health").json() == {"ok": True}
    assert client.get("/api/session").json() == {"authenticated": False}


def test_login_sets_httponly_cookie(client):
    r = client.post("/api/login", json={"password": PASSWORD})
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert client.get("/api/session").json() == {"authenticated": True}


def test_wrong_password_then_rate_limited(client):
    for _ in range(5):
        assert client.post("/api/login", json={"password": "nope"}).status_code == 401
    assert client.post("/api/login", json={"password": PASSWORD}).status_code == 429


def test_logout_clears_cookie(logged_in):
    logged_in.post("/api/logout", json={})
    assert logged_in.get("/api/session").json() == {"authenticated": False}


def test_post_must_be_json(client):
    r = client.post("/api/login", content="password=x",
                    headers={"content-type": "application/x-www-form-urlencoded"})
    assert r.status_code == 415


def test_content_route_blocks_traversal_and_non_json(logged_in):
    assert logged_in.get("/content/spec.json").status_code == 200
    assert logged_in.get("/content/../app/config.py").status_code == 404
    assert logged_in.get("/content/%2e%2e/app/config.py").status_code == 404
    assert logged_in.get("/content/EXTRACTION_NOTES.md").status_code == 404
    assert logged_in.get("/content/nope.json").status_code == 404


def test_security_headers(client):
    r = client.get("/api/health")
    assert r.headers["x-frame-options"] == "DENY"
    assert "default-src 'self'" in r.headers["content-security-policy"]
