# NOTE: avoid heavy top-level imports to optimize CLI startup times
#       (3.15 lazy imports would be nice for this)
from __future__ import annotations

import logging
from contextlib import AsyncExitStack
from functools import cache
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from quickticket.settings import Settings

log = logging.getLogger(__name__)


@click.group()
def main() -> None:
    """Start and manage the QuickTicket backend."""


@main.command(
    add_help_option=False,
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
def dev() -> None:
    """Run the `fastapi dev` command."""
    from fastapi_cli.cli import main

    main()


@main.command(
    add_help_option=False,
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
def run() -> None:
    """Run the `fastapi run` command."""
    from fastapi_cli.cli import main

    main()


@main.command()
def worker() -> None:
    """Run the task queue worker."""
    import anyio

    _setup_logging()
    anyio.run(_worker_async)


def _setup_logging() -> None:
    from quickticket.logging import setup_logging

    setup_logging(verbosity=_get_settings().log.verbosity)


@cache
def _get_settings() -> Settings:
    from quickticket.settings import Settings

    return Settings()


async def _worker_async() -> None:
    # https://github.com/adamrefaey/asynctasq/blob/ac6ca93cd2f04b1e03815c01ccf0404a11a6f773/docs/running-workers.md#programmatic-workers
    from asynctasq import Config, DriverFactory, Worker

    config = Config()
    driver = DriverFactory.create(config.driver, config)

    async with AsyncExitStack() as stack:
        await driver.connect()
        stack.push_async_callback(driver.disconnect)
        await _setup_asynctasq_sqlalchemy(stack)

        worker = Worker(
            queue_driver=driver,
            queues=["high-priority", "default", "low-priority"],
            concurrency=10,
        )

        # Start worker (blocks until SIGTERM/SIGINT)
        await worker.start()


async def _setup_asynctasq_sqlalchemy(stack: AsyncExitStack) -> None:
    # https://github.com/adamrefaey/asynctasq/blob/main/docs/orm-integrations.md#sqlalchemy
    from fastapi.datastructures import State
    from sqlalchemy import NullPool

    from quickticket.dependencies.db import AsyncEngineFactory, get_async_sessionmaker
    from quickticket.models import Base

    state = State()
    engine_factory = AsyncEngineFactory(
        engine_args={
            "poolclass": NullPool,
            "pool_pre_ping": True,
        },
    )
    engine = await engine_factory(settings=_get_settings(), stack=stack, state=state)

    Base._asynctasq_session_factory = get_async_sessionmaker(engine)
    # TODO: make sessionmaker available to tasks


if __name__ == "__main__":
    main()
