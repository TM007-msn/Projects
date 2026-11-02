"""Validation and storage of progress events.

An event looks like:
    {"id": "<uuid>", "ts": "2026-11-02T08:15:00+00:00",
     "type": "rating", "target": "1.1.1a", "data": {"value": "got"}}

Event types used so far:
    rating    data.value is "need", "once" or "got"; target is a spec point or sub-item
    verify    target is a content item id
    unverify  target is a content item id
    flag      data.note is optional free text; target is a content item id
    unflag    target is a content item id
"""

import json
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

EVENT_TYPES = {"rating", "verify", "unverify", "flag", "unflag"}
RATING_VALUES = {"need", "once", "got"}
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
TARGET_RE = re.compile(r"^[A-Za-z0-9._:-]{1,120}$")
MAX_DATA_BYTES = 2000
MAX_BATCH = 500


class Event(BaseModel):
    id: str
    ts: str
    type: str
    target: str
    data: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def check_id(cls, v: str) -> str:
        v = v.lower()
        if not UUID_RE.match(v):
            raise ValueError("id must be a UUID")
        return v

    @field_validator("ts")
    @classmethod
    def check_ts(cls, v: str) -> str:
        # Must be ISO 8601 with a timezone, so events from different devices
        # can be ordered. Stored exactly as sent.
        try:
            parsed = datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("ts must be an ISO 8601 timestamp") from exc
        if parsed.tzinfo is None:
            raise ValueError("ts must include a timezone offset")
        return v

    @field_validator("type")
    @classmethod
    def check_type(cls, v: str) -> str:
        if v not in EVENT_TYPES:
            raise ValueError(f"unknown event type {v!r}")
        return v

    @field_validator("target")
    @classmethod
    def check_target(cls, v: str) -> str:
        if not TARGET_RE.match(v):
            raise ValueError("target has invalid characters or length")
        return v

    @model_validator(mode="after")
    def check_data(self):
        if len(json.dumps(self.data)) > MAX_DATA_BYTES:
            raise ValueError("data too large")
        if self.type == "rating" and self.data.get("value") not in RATING_VALUES:
            raise ValueError("rating needs data.value of need, once or got")
        if self.type == "flag" and not isinstance(self.data.get("note", ""), str):
            raise ValueError("flag note must be text")
        return self


class EventBatch(BaseModel):
    events: list[Event] = Field(max_length=MAX_BATCH)


def insert_events(conn: sqlite3.Connection, events: list[Event]) -> dict:
    """Insert events, ignoring any whose id is already stored."""
    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    accepted = 0
    with conn:
        for e in events:
            cur = conn.execute(
                "INSERT OR IGNORE INTO events (id, client_ts, received_at, type, target, data) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (e.id, e.ts, now, e.type, e.target, json.dumps(e.data, ensure_ascii=False)),
            )
            accepted += cur.rowcount
    return {"accepted": accepted, "duplicates": len(events) - accepted}


def list_events(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, client_ts, type, target, data, received_at FROM events ORDER BY received_at, id"
    ).fetchall()
    return [
        {"id": r["id"], "ts": r["client_ts"], "type": r["type"], "target": r["target"],
         "data": json.loads(r["data"]), "received_at": r["received_at"]}
        for r in rows
    ]
