from contextlib import AsyncExitStack
from datetime import timedelta

import pytest
from fastapi.datastructures import State

from quickticket.dependencies.cache import get_cache
from quickticket.settings import CacheSettings, Settings


@pytest.mark.asyncio
async def test_sqlite_cache() -> None:
    async with AsyncExitStack() as stack:
        cache = await get_cache(
            state=State(),
            stack=stack,
            settings=Settings(cache=CacheSettings(url="sqlite:///:memory:")),
        )
        async with cache:
            assert await cache.get("a") is None

            await cache.set("a", "Hello world!")
            assert await cache.get("a") is not None

            await cache.set("a", "Hello world!", expiry=timedelta(seconds=0))
            assert await cache.get("a") is None

            await cache.set("a", "Hello world!")
            assert await cache.pop("a") == "Hello world!"
            assert await cache.get("a") is None
