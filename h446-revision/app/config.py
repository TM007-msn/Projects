"""Settings, read once from environment variables at start-up.

Required:
    APP_PASSWORD_HASH  output of `python -m app.hashpw`
    SECRET_KEY         long random string used to sign the session cookie
Optional:
    DATA_DIR           where the SQLite file lives (default ./data)
    CONTENT_DIR        where content JSON lives (default ./content)
    COOKIE_SECURE      "true" to send the cookie over HTTPS only (default false,
                       because LAN/Tailscale access is usually plain HTTP)
    SESSION_DAYS       how long a login lasts (default 30)

PORT is read by the container's start command, not here.
"""

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    password_hash: str
    secret_key: str
    data_dir: Path
    content_dir: Path
    cookie_secure: bool
    session_days: int

    @property
    def db_path(self) -> Path:
        return self.data_dir / "revision.sqlite3"


def load_settings() -> Settings:
    password_hash = os.environ.get("APP_PASSWORD_HASH", "").strip()
    secret_key = os.environ.get("SECRET_KEY", "").strip()
    if not password_hash.startswith("scrypt:"):
        raise RuntimeError("APP_PASSWORD_HASH is missing or invalid. Generate one with: python -m app.hashpw")
    if len(secret_key) < 32:
        raise RuntimeError("SECRET_KEY must be at least 32 characters. Generate one with: "
                           "python -c \"import secrets; print(secrets.token_urlsafe(48))\"")
    return Settings(
        password_hash=password_hash,
        secret_key=secret_key,
        data_dir=Path(os.environ.get("DATA_DIR", ROOT / "data")),
        content_dir=Path(os.environ.get("CONTENT_DIR", ROOT / "content")),
        cookie_secure=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
        session_days=int(os.environ.get("SESSION_DAYS", "30")),
    )
