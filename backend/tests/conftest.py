from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack
from dataclasses import dataclass

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.datastructures import State
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from quickticket.app import create_app_from_settings
from quickticket.dependencies.db import get_async_engine, get_async_sessionmaker
from quickticket.models import Base
from quickticket.settings import (
    CacheSettings,
    DatabaseSettings,
    FrontendSettings,
    LogSettings,
    OpenAPISettings,
    Settings,
)
from tests.resources import Dataset, create_test_models


@pytest.fixture
def state() -> State:
    return State()


@pytest_asyncio.fixture
async def stack() -> AsyncGenerator[AsyncExitStack]:
    async with AsyncExitStack() as stack:
        yield stack


@pytest_asyncio.fixture
async def engine(stack: AsyncExitStack, state: State) -> AsyncEngine:
    settings = Settings(
        _env_file=None,
        db=DatabaseSettings(url="sqlite+aiosqlite:///:memory:"),
    )

    engine = await get_async_engine(settings=settings, stack=stack, state=state)

    # Generate schema from models instead of running the migration scripts
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return engine


@pytest_asyncio.fixture
async def make_session(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return await get_async_sessionmaker(engine)


# Prefer explicit transactions with `make_session() as session, session.begin()`
# @pytest_asyncio.fixture
# async def session(
#     make_session: async_sessionmaker[AsyncSession],
# ) -> AsyncGenerator[AsyncSession]:
#     async with make_session.begin() as session:
#         yield session


@dataclass(kw_only=True)
class DatasetLoader:
    dataset: Dataset
    make_session: async_sessionmaker[AsyncSession]

    async def load(self) -> None:
        async with self.make_session() as session, session.begin():
            self.dataset.add_all(session)


@pytest.fixture
def dataset() -> Dataset:
    return create_test_models()


@pytest.fixture
def dataset_loader(
    dataset: Dataset,
    make_session: async_sessionmaker[AsyncSession],
) -> DatasetLoader:
    return DatasetLoader(dataset=dataset, make_session=make_session)


@pytest.fixture
def app() -> FastAPI:
    settings = Settings(
        _env_file=None,
        cache=CacheSettings(url="sqlite:///:memory:"),
        db=DatabaseSettings(url="sqlite+aiosqlite:///:memory:"),
        frontend=FrontendSettings(builtin=False),
        log=LogSettings(debug=False, profiling=False),
        openapi=OpenAPISettings(url=None),
    )
    return create_app_from_settings(settings)
