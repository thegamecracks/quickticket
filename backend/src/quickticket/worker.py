from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from asgi_lifespan import LifespanManager
from asynctasq import BaseTask, TaskExecutor
from fastapi import FastAPI
from fastapi_injectable import async_get_injected_obj, injectable, injectable_scope
from sqlalchemy import NullPool

from quickticket.app import app as app_factory
from quickticket.dependencies import db
from quickticket.dependencies.db import AsyncEngineFactory, AsyncSessionMakerDep
from quickticket.dependencies.state import get_async_exit_stack
from quickticket.models import Base


async def run_worker() -> None:
    """Start a task queue worker with the given settings."""
    # https://github.com/adamrefaey/asynctasq/blob/ac6ca93cd2f04b1e03815c01ccf0404a11a6f773/docs/running-workers.md#programmatic-workers
    from asynctasq import Config, DriverFactory, Worker  # noqa: PLC0415

    async with create_app_for_dependency_injection():
        stack = await async_get_injected_obj(get_async_exit_stack)
        await attach_asynctasq_to_models()  # ty: ignore[missing-argument]

        config = Config()
        driver = DriverFactory.create(config.driver, config)

        await driver.connect()
        stack.push_async_callback(driver.disconnect)

        worker = Worker(
            queue_driver=driver,
            queues=["high-priority", "default", "low-priority"],
            concurrency=10,
        )
        worker._task_executor = InjectableTaskExecutor()  # noqa: SLF001

        # Start worker (blocks until SIGTERM/SIGINT)
        await worker.start()


@asynccontextmanager
async def create_app_for_dependency_injection() -> AsyncGenerator[FastAPI]:
    db._engine_factory = AsyncEngineFactory(  # noqa: SLF001
        engine_args={
            "poolclass": NullPool,
            "pool_pre_ping": True,
        },
    )
    app = app_factory()
    async with LifespanManager(app):
        yield app


@injectable
async def attach_asynctasq_to_models(make_session: AsyncSessionMakerDep) -> None:
    Base._asynctasq_session_factory = make_session  # noqa: SLF001
    # HACK:
    # asynctasq is supposed to have native support for serializing ORM models
    # by primary key. However, it turns out it doesn't work with our models
    # and keeps trying to serialize the entire class.
    #
    # For models with custom types like Money and Point, this results in
    # tasks failing to serialize and dispatch.
    #
    # Here's my guess as to why it doesn't work:
    # 1. asynctasq uses the msgspec serialization library.
    # 2. msgspec natively converts dataclasses to JSON objects.
    # 3. our ORM models are marked as dataclasses.
    # 4. msgspec detects this and serializes the ORM models by its attributes,
    #    instead of calling asynctasq's encoding hook.
    #
    # Therefore, asynctasq doesn't get a chance to serialize by primary key.
    #
    # https://github.com/thegamecracks/quickticket/commit/160f9bf34d9bd831f03779ee68f3408e90176d43
    # We could make asynctasq's TypeHook classes for our custom types,
    # but that doesn't solve the root problem that msgspec won't let asynctasq
    # convert dataclass-mapped ORM models to their primary keys.


class InjectableTaskExecutor(TaskExecutor):
    """Wraps task execution with fastapi-injectable dependency cleanup."""

    async def execute(self, task: BaseTask, timeout: float | None = None) -> None:  # noqa: ASYNC109
        async with injectable_scope():
            return await super().execute(task, timeout=timeout)
