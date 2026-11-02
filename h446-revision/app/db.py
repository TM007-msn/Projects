"""SQLite storage for progress events.

The database holds one append-only table. Rows are never updated or deleted;
the app works out the current state (ratings, flags, card schedules) by
replaying events. That makes offline sync simple: a device sends the events
it has queued, and any the server already has are ignored because the event
id (a UUID made on the device) is the primary key.

Schema changes are applied in order using SQLite's PRAGMA user_version.
"""

import sqlite3
from pathlib import Path

MIGRATIONS = [
    # 1: events table
    """
    CREATE TABLE events (
        id          TEXT PRIMARY KEY,
        client_ts   TEXT NOT NULL,
        received_at TEXT NOT NULL,
        type        TEXT NOT NULL,
        target      TEXT NOT NULL,
        data        TEXT NOT NULL DEFAULT '{}'
    );
    CREATE INDEX events_received ON events(received_at);
    CREATE INDEX events_type_target ON events(type, target);
    """,
]


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # safe concurrent reads while writing
    conn.execute("PRAGMA foreign_keys=ON")
    migrate(conn)
    return conn


def migrate(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    for number, sql in enumerate(MIGRATIONS[version:], start=version + 1):
        with conn:
            conn.executescript(sql)
            conn.execute(f"PRAGMA user_version = {number}")
