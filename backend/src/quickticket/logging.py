"""Handle logging configuration.

Derived from the discord.utils module in discord.py 2.7.1.

"""

import logging
import os
from enum import IntEnum
from functools import cache

from rich.console import Console
from rich.logging import RichHandler


class LogVerbosity(IntEnum):
    MINIMAL = 0
    """Only show warning logs and errors."""
    PROJECT_INFO = 1
    """Show info logs from this package."""
    GLOBAL_INFO = 2
    """Show info logs from all packages."""
    PROJECT_DEBUG = 3
    """Show debug logs from this package."""
    PROJECT_QUERIES = 4
    """Show SQLAlchemy queries. Includes sensitive information!"""
    GLOBAL_DEBUG = 5
    """Show debug logs from all dependencies. Very noisy!"""


def setup_logging(*, verbosity: LogVerbosity) -> None:
    root_level = logging.WARNING
    project_level = logging.NOTSET
    sqlalchemy_level = logging.NOTSET

    if verbosity >= LogVerbosity.PROJECT_INFO:
        project_level = logging.INFO
    if verbosity >= LogVerbosity.GLOBAL_INFO:
        root_level = logging.INFO
    if verbosity >= LogVerbosity.PROJECT_DEBUG:
        project_level = logging.DEBUG
    if verbosity >= LogVerbosity.PROJECT_QUERIES:
        sqlalchemy_level = logging.INFO
    if verbosity >= LogVerbosity.GLOBAL_DEBUG:
        root_level = logging.DEBUG

    handler = RichHandler(
        console=Console(
            # HACK: in docker, compensate for docker compose's prefix
            width=int(os.getenv("COLUMNS") or 148) - (28 * is_docker()),
            soft_wrap=is_docker(),
        ),
        rich_tracebacks=True,
        tracebacks_suppress=[
            "fastapi",
            "starlette",
        ],
        log_time_format="[%Y-%m-%d %H:%M:%S]",
    )
    formatter = logging.Formatter(
        fmt="{message}",
        datefmt="[%Y-%m-%d %H:%M:%S]",
        style="{",
    )

    logger = logging.getLogger()
    handler.setFormatter(formatter)
    logger.setLevel(root_level)
    logger.addHandler(handler)

    logging.getLogger(__package__).setLevel(project_level)
    logging.getLogger("sqlalchemy.engine").setLevel(sqlalchemy_level)


@cache
def is_docker() -> bool:
    path = "/proc/self/cgroup"
    return os.path.exists("/.dockerenv") or (
        os.path.isfile(path) and any("docker" in line for line in open(path))
    )
