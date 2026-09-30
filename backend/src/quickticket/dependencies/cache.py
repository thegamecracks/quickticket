import logging
from typing import Annotated, cast

import aiosqlite
from fastapi import Depends
from redis.asyncio import Redis

from quickticket.cache import Cache, RedisCache, SQLiteCache
from quickticket.dependencies.state import AsyncExitStackDep, SettingsDep, StateDep

log = logging.getLogger(__name__)


async def get_cache(
    state: StateDep,
    stack: AsyncExitStackDep,
    settings: SettingsDep,
) -> Cache:
    cache = cast(Cache | None, getattr(state, "cache", None))
    if cache is not None:
        return cache

    url = settings.cache.url.get_secret_value()
    if url.scheme == "sqlite":
        assert url.path is not None
        conn = await aiosqlite.connect(
            url.path[1:],
            autocommit=True,
            uri=True,
        )
        state.cache = await stack.enter_async_context(SQLiteCache(conn))
    elif url.scheme in ("redis", "rediss"):
        assert url.host is not None
        assert url.port is not None
        client = Redis(
            host=url.host,
            port=url.port,
            username=url.username,
            password=url.password,
            ssl=url.scheme == "rediss",
        )
        state.cache = await stack.enter_async_context(RedisCache(client))
    else:
        raise ValueError(f"Unsupported url scheme for cache: {url.scheme}")

    log.info("Initialized %s", type(state.cache).__name__)
    return state.cache


CacheDep = Annotated[Cache, Depends(get_cache)]
