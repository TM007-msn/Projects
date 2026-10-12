from collections.abc import Iterator
from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401  (registers the tables)

engine = None


def configure(url: str) -> None:
    """Create the engine and tables. Called once at startup (and by tests with an in-memory DB)."""
    global engine
    kwargs: dict = {"connect_args": {"check_same_thread": False}}
    if url in ("sqlite://", "sqlite:///:memory:"):
        kwargs["poolclass"] = StaticPool  # one shared in-memory DB across threads
    elif url.startswith("sqlite:///"):
        Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(url, **kwargs)
    SQLModel.metadata.create_all(engine)


def new_session() -> Session:
    return Session(engine)


def get_session() -> Iterator[Session]:
    """FastAPI dependency."""
    with Session(engine) as session:
        yield session
