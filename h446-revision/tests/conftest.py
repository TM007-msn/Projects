"""Shared pytest fixtures: an app with a throwaway database and a known password."""

import pytest
from fastapi.testclient import TestClient

from app.auth import hash_password
from app.config import ROOT, Settings
from app.main import create_app

PASSWORD = "correct horse battery"
HASH = hash_password(PASSWORD)  # computed once; scrypt is deliberately slow


@pytest.fixture
def settings(tmp_path):
    return Settings(password_hash=HASH, secret_key="x" * 40, data_dir=tmp_path,
                    content_dir=ROOT / "content", cookie_secure=False, session_days=30)


@pytest.fixture
def client(settings):
    return TestClient(create_app(settings))


@pytest.fixture
def logged_in(client):
    r = client.post("/api/login", json={"password": PASSWORD})
    assert r.status_code == 200
    return client
