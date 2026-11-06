"""Insert test data into the configured database from settings."""
# Invoke with `uv run python -m tests.scripts.insert_data`

import argparse
import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from functools import cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from quickticket.logging import LogVerbosity, setup_logging
from quickticket.settings import Settings
from tests.dataset import create_test_models

log = logging.getLogger(__name__)


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-y", "--yes", action="store_true", help="Confirm")

    args = parser.parse_args()
    yes: bool = args.yes
    setup_logging(verbosity=LogVerbosity.PROJECT_DEBUG)
    log.setLevel(logging.DEBUG)

    async with start_sessionmaker() as make_session, make_session.begin() as session:
        if not yes:
            return log.info("Run with -y/--yes to confirm")

        await run_queries(session)


async def run_queries(session: AsyncSession) -> None:
    dataset = create_test_models()
    await dataset.merge_all(session)


@asynccontextmanager
async def start_sessionmaker() -> AsyncGenerator[async_sessionmaker]:
    engine = create_async_engine(get_database_url())
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()


@cache
def get_database_url() -> str:
    url = Settings().db.url.get_secret_value()
    clean_url = url.build(
        scheme=url.scheme,
        host=url.host or "",
        port=url.port,
        path=(url.path or "").removeprefix("/"),
        query=url.query,
        fragment=url.fragment,
    )
    log.info("Selected database: %s", clean_url)
    return str(url)


if __name__ == "__main__":
    asyncio.run(main())
