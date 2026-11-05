from contextlib import AsyncExitStack

import pytest
from fastapi.datastructures import State
from sqlalchemy.ext.asyncio import AsyncEngine

from quickticket.dependencies.db import AsyncEngineFactory, get_async_sessionmaker
from quickticket.settings import DatabaseSettings, Settings


@pytest.mark.asyncio
async def test_engine_factory_reuses_engine(stack: AsyncExitStack, state: State) -> None:
    settings = Settings(
        _env_file=None,
        db=DatabaseSettings(url="sqlite+aiosqlite:///:memory:"),
    )

    engine_factory = AsyncEngineFactory()
    engine_1 = await engine_factory(settings=settings, stack=stack, state=state)
    engine_2 = await engine_factory(settings=settings, stack=stack, state=state)

    assert engine_1 is engine_2


@pytest.mark.asyncio
async def test_get_async_sessionmaker_reuses_sessionmaker(
    state: State,
    engine: AsyncEngine,
) -> None:
    make_session_1 = await get_async_sessionmaker(state, engine)
    make_session_2 = await get_async_sessionmaker(state, engine)
    assert make_session_1 is make_session_2
