from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import inspect, text
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401  (registers every table on SQLModel.metadata)
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


def _sqlite_literal(column) -> str:
    default = column.default
    value = getattr(default, "arg", None) if default is not None else None
    if callable(value):
        value = None
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def migrate() -> list[str]:
    """Add columns that new releases introduced.

    SQLModel's create_all only ever creates whole tables, so a panel upgraded in
    place keeps its old column set. Walking the metadata and issuing ALTER TABLE
    for what is missing keeps upgrades to `git pull && systemctl restart`.
    """
    applied: list[str] = []
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for name, table in SQLModel.metadata.tables.items():
            if name not in existing_tables:
                continue
            present = {col["name"] for col in inspector.get_columns(name)}
            for column in table.columns:
                if column.name in present:
                    continue
                kind = column.type.compile(dialect=engine.dialect)
                statement = f'ALTER TABLE "{name}" ADD COLUMN "{column.name}" {kind}'
                if not column.nullable:
                    statement += f" NOT NULL DEFAULT {_sqlite_literal(column)}"
                connection.execute(text(statement))
                applied.append(f"{name}.{column.name}")
    return applied


def init_db() -> list[str]:
    SQLModel.metadata.create_all(engine)
    return migrate()


def get_session() -> Iterator[Session]:
    with Session(engine, expire_on_commit=False) as session:
        yield session
