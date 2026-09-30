from collections.abc import AsyncIterator
from typing import Annotated, cast

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from quickticket.dependencies.state import AsyncExitStackDep, SettingsDep, StateDep

__all__ = (
    "AsyncEngineDep",
    "AsyncSessionDep",
)


async def get_async_engine(
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


async def get_async_session(engine: AsyncEngineDep) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(engine) as session:
        yield session


AsyncEngineDep = Annotated[AsyncEngine, Depends(get_async_engine)]
AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
