from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack
from dataclasses import dataclass
from functools import partial
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from asynctasq import AsyncTasQIntegration, Dispatcher
from asynctasq.drivers import BaseDriver
from fastapi import FastAPI
from fastapi.datastructures import State
from fastapi_injectable import cleanup_all_exit_stacks, clear_dependency_cache
from httpx2 import ASGITransport, AsyncClient
from obstore.store import MemoryStore
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from quickticket.app import create_app_from_settings
from quickticket.dependencies.auth import get_user
from quickticket.dependencies.db import AsyncEngineFactory, _engine_factory, get_async_sessionmaker
from quickticket.dependencies.state import get_settings
from quickticket.dependencies.store import Store, get_object_store
from quickticket.models import Address, Base, User
from quickticket.settings import (
    CacheSettings,
    DatabaseSettings,
    FrontendSettings,
    LogSettings,
    OpenAPISettings,
    SecuritySettings,
    Settings,
)
from tests.dataset import Dataset, create_test_models


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

    engine_factory = AsyncEngineFactory()
    engine = await engine_factory(settings=settings, stack=stack, state=state)

    # Generate schema from models instead of running the migration scripts
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    return engine


@pytest_asyncio.fixture
async def make_session(state: State, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return await get_async_sessionmaker(state, engine)


# Prefer explicit transactions with `make_session.begin() as session`
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
        async with self.make_session.begin() as session:
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


@dataclass(kw_only=True)
class AuthController:
    """The authenication fake used by the app fixture.

    When enabled (the default), dependencies on OptionalUserDep will return
    :attr:`user` regardless of authentication headers/cookies, so tests don't
    need to pass cookies in.

    """

    enabled: bool = True
    """Whether authentication faking is enabled."""

    user: User | None = None
    """The currently authenticated user. Can be mutated in-place."""

    def get_user(self) -> User | None:
        if self.enabled:
            return self.user
        raise NotImplementedError  # TODO: resolve get_user() with FastAPI's DI framework


@pytest.fixture
def auth() -> AuthController:
    return AuthController()


@pytest.fixture
def store() -> Store:
    return MemoryStore()


@pytest.fixture(scope="session")
def _base_app() -> FastAPI:
    # This caches the base ASGI app per test session which drastically improves performance.
    # Tests use the app fixture which supplies per-function fixtures like the engine.
    settings = Settings(
        _env_file=None,
        cache=CacheSettings(url="sqlite:///:memory:"),
        # The database URL is intentionally broken to raise the exception:
        #
        #     sqlalchemy.exc.ArgumentError: Could not parse SQLAlchemy URL from given URL string
        #
        # Using dependency overrides, there should not be any calls to AsyncEngineFactory()
        # other than our fixture which makes in-memory databases pre-initialized with our schema.
        db=DatabaseSettings(url="sqlite+aiosqlite:/"),
        frontend=FrontendSettings(builtin=False),
        log=LogSettings(debug=False, profiling=False),
        openapi=OpenAPISettings(url=None),
        security=SecuritySettings(allowed_hosts=["*"]),
    )
    app = create_app_from_settings(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    return app


@pytest.fixture(autouse=True)
def asynctasq_dispatcher(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    # https://github.com/adamrefaey/asynctasq/blob/ac6ca93cd2f04b1e03815c01ccf0404a11a6f773/tests/unit/tasks/types/test_function_task.py#L281-L301
    mock_dispatcher = AsyncMock(Dispatcher)
    mock_dispatcher.dispatch = AsyncMock(return_value="task-id-123")
    monkeypatch.setattr("asynctasq.core.dispatcher.get_dispatcher", lambda *_: mock_dispatcher)
    return mock_dispatcher


@pytest.fixture(autouse=True)
def asynctasq_driver(
    monkeypatch: pytest.MonkeyPatch,
    asynctasq_dispatcher: AsyncMock,
) -> MagicMock:
    # https://github.com/adamrefaey/asynctasq/blob/ac6ca93cd2f04b1e03815c01ccf0404a11a6f773/tests/unit/integrations/test_fastapi.py#L21-L27
    mock_driver = MagicMock(BaseDriver)
    mock_driver.connect = AsyncMock()
    mock_driver.disconnect = AsyncMock()
    integration = partial(AsyncTasQIntegration, driver=mock_driver)
    monkeypatch.setattr("quickticket.app.AsyncTasQIntegration", integration)
    monkeypatch.setattr(
        "asynctasq.integrations.fastapi.Dispatcher",
        lambda driver: asynctasq_dispatcher,
    )
    asynctasq_dispatcher.driver = mock_driver
    return mock_driver


@pytest_asyncio.fixture
async def app(
    monkeypatch: pytest.MonkeyPatch,
    _base_app: FastAPI,
    stack: AsyncExitStack,
    engine: AsyncEngine,
    make_session: async_sessionmaker[AsyncSession],
    auth: AuthController,
    store: Store,
) -> AsyncGenerator[FastAPI]:
    # Technically we should cleanup our overrides after a test, but they'll get overwritten anyway
    _base_app.dependency_overrides[_engine_factory] = lambda: engine
    _base_app.dependency_overrides[get_async_sessionmaker] = lambda: make_session
    _base_app.dependency_overrides[get_object_store] = lambda: store
    _base_app.dependency_overrides[get_user] = auth.get_user

    async with make_session.begin() as session:
        auth.user = User(
            display_name="Test User",
            first_name="Test",
            last_name="User",
            email="test.user@example.com",
            addresses=[
                Address(
                    line_1="123 Test Street",
                    line_2="Unit 4",
                    city="Testville",
                    province="Ontario",
                    postal_code="A1B 2C3",
                )
            ],
        )
        session.add(auth.user)

    monkeypatch.setattr("quickticket.app.AsyncExitStack", lambda: stack)
    try:
        async with LifespanManager(_base_app):
            yield _base_app
    finally:
        # Reset dependencies for @injectable functions
        # https://github.com/JasperSui/fastapi-injectable/blob/v1.6.2/src/fastapi_injectable/pytest_plugin.py
        await cleanup_all_exit_stacks()
        await clear_dependency_cache()


# https://fastapi.tiangolo.com/advanced/async-tests/
@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app), base_url="http://test") as client:
        yield client
