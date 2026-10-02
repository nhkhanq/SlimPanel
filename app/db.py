from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

_connect_args = {"check_same_thread": False}

if str(settings.db_path) == ":memory:":
    engine = create_engine(
        "sqlite://", connect_args=_connect_args, poolclass=StaticPool, echo=False
    )
else:
    settings.ensure_dirs()
    engine = create_engine(
        f"sqlite:///{settings.db_path}", connect_args=_connect_args, echo=False
    )


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine, expire_on_commit=False) as session:
        yield session
