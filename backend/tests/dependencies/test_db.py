from contextlib import AsyncExitStack, asynccontextmanager

import pytest
from fastapi import Response
from fastapi.datastructures import State
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.sql.functions import count

from quickticket.dependencies.db import (
    AsyncEngineFactory,
    get_async_session,
    get_async_sessionmaker,
)
from quickticket.errors import ForcedResponse
from quickticket.models import User
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


enter_get_async_session = asynccontextmanager(get_async_session)


def create_user() -> User:
    return User(
        display_name="Test User",
        first_name="Test",
        last_name="User",
        email="test.user@example.com",
    )


async def count_users(session: AsyncSession) -> int:
    ret = await session.scalar(select(count()).select_from(User))
    assert ret is not None
    return ret


@pytest.mark.asyncio
async def test_get_async_session_commits(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    async with enter_get_async_session(make_session) as session:
        session.add(create_user())

    async with make_session.begin() as session:
        assert await count_users(session) == 1


@pytest.mark.asyncio
async def test_get_async_session_rolls_back_on_error(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    with pytest.raises(RuntimeError, match=r"^rollback$"):  # noqa: PT012
        async with enter_get_async_session(make_session) as session:
            session.add(create_user())
            raise RuntimeError("rollback")

    async with make_session.begin() as session:
        assert await count_users(session) == 0


@pytest.mark.asyncio
async def test_get_async_session_commits_on_forced_response(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    forced_response = ForcedResponse(Response())

    with pytest.raises(ForcedResponse) as exc_info:  # noqa: PT012
        async with enter_get_async_session(make_session) as session:
            session.add(create_user())
            raise forced_response

    assert exc_info.value is forced_response
    async with make_session.begin() as session:
        assert await count_users(session) == 1


@pytest.mark.asyncio
async def test_get_async_session_returns_aware_datetimes(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    async with enter_get_async_session(make_session) as session:
        session.add(create_user())

    async with make_session.begin() as session:
        user = await session.scalar(select(User))
        assert user is not None
        # The TZDateTime converter coerces the database's naive timestamps.
        assert user.created_at.tzinfo is not None
