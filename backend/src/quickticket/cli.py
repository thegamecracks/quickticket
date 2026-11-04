import logging
from functools import cache

import click
from fastapi_cli.cli import main as fastapi_main

from quickticket.logging import setup_logging
from quickticket.settings import Settings
from quickticket.worker import run_worker

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
    fastapi_main()


@main.command(
    add_help_option=False,
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
def run() -> None:
    """Run the `fastapi run` command."""
    fastapi_main()


@main.command()
def worker() -> None:
    """Run the task queue worker."""
    import anyio

    _setup_logging()
    anyio.run(run_worker, _get_settings())


def _setup_logging() -> None:
    setup_logging(verbosity=_get_settings().log.verbosity)


@cache
def _get_settings() -> Settings:
    return Settings()


if __name__ == "__main__":
    main()
