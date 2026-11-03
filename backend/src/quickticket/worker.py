from contextlib import AsyncExitStack

from fastapi.datastructures import State
from sqlalchemy import NullPool

from quickticket.dependencies.db import (
    AsyncEngineFactory,
    get_async_sessionmaker as _get_async_sessionmaker,
)
from quickticket.settings import Settings
from quickticket.tasks.engine import register_async_engine, register_async_sessionmaker


async def run_worker(settings: Settings) -> None:
    """Start a task queue worker with the given settings."""
    # https://github.com/adamrefaey/asynctasq/blob/ac6ca93cd2f04b1e03815c01ccf0404a11a6f773/docs/running-workers.md#programmatic-workers
    from asynctasq import Config, DriverFactory, Worker

    config = Config()
    driver = DriverFactory.create(config.driver, config)

    async with AsyncExitStack() as stack:
        await driver.connect()
        stack.push_async_callback(driver.disconnect)

        await _create_engine_for_tasks(settings, stack)

        worker = Worker(
            queue_driver=driver,
            queues=["high-priority", "default", "low-priority"],
            concurrency=10,
        )

        # Start worker (blocks until SIGTERM/SIGINT)
        await worker.start()


async def _create_engine_for_tasks(settings: Settings, stack: AsyncExitStack) -> None:
    # https://github.com/adamrefaey/asynctasq/blob/main/docs/orm-integrations.md#sqlalchemy
    engine_factory = AsyncEngineFactory(
        engine_args={
            "poolclass": NullPool,
            "pool_pre_ping": True,
        },
    )
    engine = await engine_factory(settings=settings, stack=stack, state=State())
    make_session = await _get_async_sessionmaker(engine)

    # Store as global state for tasks to access
    register_async_engine(engine)
    register_async_sessionmaker(make_session)
