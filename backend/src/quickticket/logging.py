"""Handle logging configuration.

Derived from the discord.utils module in discord.py 2.7.1.

"""

import logging
import os
import sys
from enum import IntEnum
from typing import Any, ClassVar


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

    handler = logging.StreamHandler()
    if stream_supports_colour(handler.stream):
        formatter = _ColourFormatter()
    else:
        dt_fmt = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(
            "[{asctime}] [{levelname:<8}] {name}: {message}",
            dt_fmt,
            style="{",
        )

    logger = logging.getLogger()
    handler.setFormatter(formatter)
    logger.setLevel(root_level)
    logger.addHandler(handler)

    # # NOTE: Logging propagation only applies to handlers and not filters,
    # #       so root.addFilter() won't catch logs from all loggers.
    # #       We need to add filters directly to each package's logger.
    # logging.getLogger("discord.client").addFilter(
    #     lambda r: not r.getMessage().endswith("voice will NOT be supported")
    # )
    # logging.getLogger("discord.gateway").addFilter(
    #     lambda r: "has successfully RESUMED session" not in r.getMessage()
    # )

    logging.getLogger(__package__).setLevel(project_level)
    logging.getLogger("sqlalchemy.engine").setLevel(sqlalchemy_level)


def stream_supports_colour(stream: Any) -> bool:
    # https://force-color.org/
    if os.getenv("FORCE_COLOR"):
        return True
    elif os.getenv("NO_COLOR"):
        return False

    is_a_tty = hasattr(stream, "isatty") and stream.isatty()

    # Pycharm and Vscode support colour in their inbuilt editors
    if "PYCHARM_HOSTED" in os.environ or os.environ.get("TERM_PROGRAM") == "vscode":
        return is_a_tty

    if sys.platform != "win32":
        # Docker does not consistently have a tty attached to it
        return is_a_tty or _is_docker()

    # ANSICON checks for things like ConEmu
    # WT_SESSION checks if this is Windows Terminal
    return is_a_tty and ("ANSICON" in os.environ or "WT_SESSION" in os.environ)


def _is_docker() -> bool:
    path = "/proc/self/cgroup"
    return os.path.exists("/.dockerenv") or (
        os.path.isfile(path) and any("docker" in line for line in open(path))
    )


class _ColourFormatter(logging.Formatter):
    # ANSI codes are a bit weird to decipher if you're unfamiliar with them, so here's a refresher
    # It starts off with a format like \x1b[XXXm where XXX is a semicolon separated list of commands
    # The important ones here relate to colour.
    # 30-37 are black, red, green, yellow, blue, magenta, cyan and white in that order
    # 40-47 are the same except for the background
    # 90-97 are the same but "bright" foreground
    # 100-107 are the same as the bright ones but for the background.
    # 1 means bold, 2 means dim, 0 means reset, and 4 means underline.

    LEVEL_COLOURS: ClassVar[list[tuple[int, str]]] = [
        (logging.DEBUG, "\x1b[40;1m"),
        (logging.INFO, "\x1b[34;1m"),
        (logging.WARNING, "\x1b[33;1m"),
        (logging.ERROR, "\x1b[31m"),
        (logging.CRITICAL, "\x1b[41m"),
    ]

    FORMATS: ClassVar[dict[int, logging.Formatter]] = {
        level: logging.Formatter(
            f"\x1b[30;1m%(asctime)s\x1b[0m {colour}%(levelname)-8s\x1b[0m \x1b[35m%(name)s\x1b[0m %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        for level, colour in LEVEL_COLOURS
    }

    def format(self, record):
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Override the traceback to always print in red
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f"\x1b[31m{text}\x1b[0m"

        output = formatter.format(record)

        # Remove the cache layer
        record.exc_text = None
        return output
