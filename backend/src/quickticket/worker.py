from collections.abc import Mapping
from contextlib import AsyncExitStack
from typing import Any

from asynctasq import (
    HookRegistry,
    MsgspecSerializer,
    TypeHook,
)
from asynctasq.core.dispatcher import get_dispatcher
from sqlalchemy import Dialect, NullPool
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from quickticket.dependencies.db import (
    AsyncEngineFactory,
    get_async_sessionmaker as _get_async_sessionmaker,
)
from quickticket.models import Base, Money, MoneySerializer, Point, PointSerializer
from quickticket.settings import Settings

# Ergh, global state for asynctasq
_engine: AsyncEngine | None = None
_make_session: async_sessionmaker[AsyncSession] | None = None


async def run_worker(settings: Settings) -> None:
    """Start a task queue worker with the given settings."""
    # https://github.com/adamrefaey/asynctasq/blob/ac6ca93cd2f04b1e03815c01ccf0404a11a6f773/docs/running-workers.md#programmatic-workers
    from asynctasq import Config, DriverFactory, Worker

    config = Config()
    driver = DriverFactory.create(config.driver, config)

    serializer = MsgspecSerializer()
    register_type_hooks(registry=None)
    register_type_hooks(registry=serializer.registry)

    async with AsyncExitStack() as stack:
        await driver.connect()
        stack.push_async_callback(driver.disconnect)

        await _init_sqlalchemy_from_settings(settings, stack)

        worker = Worker(
            queue_driver=driver,
            queues=["high-priority", "default", "low-priority"],
            concurrency=10,
            serializer=serializer,
        )

        # Start worker (blocks until SIGTERM/SIGINT)
        await worker.start()


async def _init_sqlalchemy_from_settings(settings: Settings, stack: AsyncExitStack) -> None:
    # https://github.com/adamrefaey/asynctasq/blob/main/docs/orm-integrations.md#sqlalchemy
    from fastapi.datastructures import State

    engine_factory = AsyncEngineFactory(
        engine_args={
            "poolclass": NullPool,
            "pool_pre_ping": True,
        },
    )
    engine = await engine_factory(settings=settings, stack=stack, state=State())
    make_session = await _get_async_sessionmaker(engine)
    register_async_engine(engine)
    register_async_sessionmaker(make_session)


def register_async_engine(engine: AsyncEngine) -> None:
    """Register an async engine for the task queue worker."""
    global _engine
    _engine = engine


def register_async_sessionmaker(make_session: async_sessionmaker[AsyncSession]) -> None:
    """Register an async sessionmaker for the task queue worker."""
    global _make_session
    _make_session = make_session
    Base._asynctasq_session_factory = make_session


def get_async_engine() -> AsyncEngine:
    """Get the async engine used by the task queue worker."""
    if _engine is None:
        raise RuntimeError("AsyncEngine not registered with register_async_engine()")
    return _engine


def get_async_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Get the async sessionmaker used by the task queue worker."""
    if _make_session is None:
        raise RuntimeError("Sessionmaker not registered with register_async_sessionmaker()")
    return _make_session


def register_type_hooks(*, registry: HookRegistry | None) -> None:
    """Register type hooks on asynctasq to allow de/serializing our custom data types."""
    # https://github.com/adamrefaey/asynctasq/blob/ac6ca93cd2f04b1e03815c01ccf0404a11a6f773/src/asynctasq/serializers/hooks/__init__.py
    if registry is None:
        # Default registry used when dispatching tasks
        registry = get_dispatcher().serializer.registry

    registry.register(MoneyTypeHook())
    registry.register(PointTypeHook())


class MoneyTypeHook(TypeHook[Money]):
    type_key = "__money__"

    def __init__(self) -> None:
        self._serializer = MoneySerializer()
        self._dialect = Dialect()

    def can_encode(self, obj: object):
        return isinstance(obj, Money)

    def encode(self, obj: Money):
        return {self.type_key: self._serializer.process_bind_param(obj, self._dialect)}

    def decode(self, data: Mapping[str, Any]):
        return self._serializer.process_result_value(data[self.type_key], self._dialect)


class PointTypeHook(TypeHook[Point]):
    type_key = "__point__"

    def __init__(self) -> None:
        self._serializer = PointSerializer()
        self._dialect = Dialect()

    def can_encode(self, obj: object):
        return isinstance(obj, Point)

    def encode(self, obj: Point):
        return {self.type_key: self._serializer.process_bind_param(obj, self._dialect)}

    def decode(self, data: Mapping[str, Any]):
        return self._serializer.process_result_value(data[self.type_key], self._dialect)
