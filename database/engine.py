from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import config

from .base import Base


def _configure_sqlite_connection(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
    finally:
        cursor.close()


def create_project_engine(database_url: str, *, echo: bool) -> AsyncEngine:
    project_engine = create_async_engine(database_url, echo=echo, future=True)
    if make_url(database_url).get_backend_name() == "sqlite":
        event.listen(
            project_engine.sync_engine,
            "connect",
            _configure_sqlite_connection,
        )
    return project_engine


engine = create_project_engine(config.DATABASE_URL, echo=config.DEBUG)

session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_tables() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

