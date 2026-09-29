from __future__ import annotations

from functools import cache
from typing import Annotated

import aiosqlite
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import Depends, HTTPException, Request
from redis.asyncio import Redis

from quickticket.cache import Cache, RedisCache, SQLiteCache
from quickticket.settings import Settings

# TODO: close cache cleanly / context manager or lifespan?
_cache_client: Cache | None = None
async def get_cache(settings: SettingsDep) -> Cache:
    global _cache_client
    if _cache_client is not None:
        return _cache_client

    url = settings.cache.url.get_secret_value()
    if url.scheme == "sqlite":
        assert url.path is not None
        conn = await aiosqlite.connect(
            url.path[1:],
            autocommit=True,
            uri=True,
        )
        _cache_client = SQLiteCache(conn)
    elif url.scheme == "redis":
        assert url.host is not None
        assert url.port is not None
        client = Redis(
            host=url.host,
            port=url.port,
            username=url.username,
            password=url.password,
            # TODO: support ssl
        )
        _cache_client = RedisCache(client)
    else:
        raise ValueError(f"Unsupported url scheme for cache: {url.scheme}")

    return _cache_client


@cache
def get_oauth_client(request: Request, settings: SettingsDep) -> AsyncOAuth2Client:
    if settings.oauth is None:
        raise HTTPException(404, "OAuth2 is not configured for this backend")

    return AsyncOAuth2Client(
        client_id=settings.oauth.client_id,
        client_secret=settings.oauth.client_secret,
        redirect_uri=request.app.url_path_for("/auth/callback"),
        scope="openid email profile",
    )


@cache
def get_settings() -> Settings:
    return Settings()


AsyncOAuth2ClientDep = Annotated[AsyncOAuth2Client, Depends(get_oauth_client)]
CacheDep = Annotated[Cache, Depends(get_cache)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
