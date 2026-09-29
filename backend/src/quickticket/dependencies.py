from __future__ import annotations

import logging
from contextlib import AsyncExitStack
from functools import cache
from typing import Annotated, cast

import aiosqlite
import httpx2
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.datastructures import State
from redis.asyncio import Redis

from quickticket.cache import Cache, RedisCache, SQLiteCache
from quickticket.oauth import OAuth2Client, OpenIDDiscoveryProvider
from quickticket.settings import Settings

log = logging.getLogger(__name__)


def get_state(request: Request) -> State:
    return cast(FastAPI, request.app).state


def get_async_exit_stack(state: StateDep) -> AsyncExitStack:
    return cast(AsyncExitStack, state.stack)


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
        state.cache = await stack.enter_async_context(RedisCache(client))
    else:
        raise ValueError(f"Unsupported url scheme for cache: {url.scheme}")

    return state.cache


async def get_oauth_client(
    request: Request,
    state: StateDep,
    settings: SettingsDep,
) -> OAuth2Client:
    client = cast(OAuth2Client | None, getattr(state, "oauth_client", None))
    if client is not None:
        return client

    if settings.openid is None:
        raise HTTPException(404, "OpenID is not configured for this backend")

    # FIXME: exceptions here can result in spamming the discovery URL
    print("Fetching OpenID discovery url")
    async with httpx2.AsyncClient() as http:
        response = await http.get(str(settings.openid.discovery_url))
        response = response.json()

    print("Creating OAuth2 client")
    provider = OpenIDDiscoveryProvider.model_validate(response)
    state.oauth_client = OAuth2Client(
        client_id=settings.openid.client_id.get_secret_value(),
        client_secret=settings.openid.client_secret.get_secret_value(),
        redirect_uri=str(request.url_for("oauth_callback")),
        provider=provider,
    )
    return state.oauth_client


@cache
def get_settings() -> Settings:
    return Settings()


AsyncExitStackDep = Annotated[AsyncExitStack, Depends(get_async_exit_stack)]
CacheDep = Annotated[Cache, Depends(get_cache)]
OAuth2ClientDep = Annotated[OAuth2Client, Depends(get_oauth_client)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
StateDep = Annotated[State, Depends(get_state)]
