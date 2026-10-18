import logging
from collections.abc import AsyncGenerator
from typing import Annotated, Any, cast

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from quickticket.dependencies.state import AsyncExitStackDep, SettingsDep, StateDep
from quickticket.errors import ForcedResponse

__all__ = (
    "AsyncEngineDep",
    "AsyncSessionDep",
    "AsyncSessionMakerDep",
    "get_async_engine",
    "get_async_session",
    "get_async_sessionmaker",
)

log = logging.getLogger(__name__)


async def get_async_engine(
    settings: SettingsDep,
    stack: AsyncExitStackDep,
    state: StateDep,
) -> AsyncEngine:
    engine = cast(AsyncEngine | None, getattr(state, "engine", None))
    if engine is not None:
        return engine

    url = str(settings.db.url.get_secret_value())

    connect_args: dict[str, Any] = {}
    if url.startswith("sqlite"):
        # https://docs.sqlalchemy.org/en/21/dialects/sqlite.html#enabling-non-legacy-sqlite-transactional-modes-with-the-sqlite3-or-aiosqlite-driver
        connect_args["autocommit"] = False

    state.engine = create_async_engine(url, connect_args=connect_args)
    stack.push_async_callback(state.engine.dispose)
    return state.engine


async def get_async_sessionmaker(
    engine: AsyncEngineDep,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session(
    make_session: AsyncSessionMakerDep,
) -> AsyncGenerator[AsyncSession]:
    async with make_session.begin() as session:
        try:
            yield session
        except ForcedResponse:
            # Response is being sent, assume the caller wants us to commit
            await session.commit()
            raise


AsyncEngineDep = Annotated[AsyncEngine, Depends(get_async_engine)]
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session, scope="function")]
AsyncSessionMakerDep = Annotated[async_sessionmaker[AsyncSession], Depends(get_async_sessionmaker)]
