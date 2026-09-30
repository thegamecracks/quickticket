import logging
from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from quickticket.dependencies.state import AsyncExitStackDep, SettingsDep, StateDep
from quickticket.errors import ForcedResponse

log = logging.getLogger(__name__)


def get_async_engine(
    settings: SettingsDep,
    stack: AsyncExitStackDep,
    state: StateDep,
) -> AsyncEngine:
    engine = cast(AsyncEngine | None, getattr(state, "engine", None))
    if engine is not None:
        return engine

    url = str(settings.db.url.get_secret_value())
    state.engine = create_async_engine(url)
    stack.push_async_callback(state.engine.dispose)
    return state.engine


def get_async_sessionmaker(
    engine: AsyncEngineDep,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_async_session(
    make_session: AsyncSessionMakerDep,
) -> AsyncIterator[AsyncSession]:
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
