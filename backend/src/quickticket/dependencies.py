from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack
from functools import cache
from typing import Annotated, cast

import aiosqlite
import httpx2
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.datastructures import State
from fastapi.security import OAuth2PasswordBearer
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import KeySet
from joserfc.jwt import Token
from redis.asyncio import Redis

from quickticket.cache import Cache, RedisCache, SQLiteCache
from quickticket.oauth import OAuth2Client, OpenIDProvider
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


async def get_http_client() -> AsyncIterator[httpx2.AsyncClient]:
    async with httpx2.AsyncClient() as client:
        yield client


async def get_openid_provider(
    http: HTTPClientDep,
    state: StateDep,
    settings: SettingsDep,
) -> OpenIDProvider:
    provider = cast(
        OpenIDProvider | None,
        getattr(state, "openid_provider", None),
    )
    if provider is not None:
        return provider

    if settings.openid is None:
        raise HTTPException(404, "OpenID is not configured for this backend")

    # FIXME: exceptions here can result in spamming the discovery URL
    print("Fetching OpenID discovery url")
    response = await http.get(str(settings.openid.discovery_url))
    state.openid_provider = OpenIDProvider(
        client_id=settings.openid.client_id,
        client_secret=settings.openid.client_secret,
        discovery=response.json(),
    )

    return state.openid_provider


async def get_openid_provider_jwks(
    http: HTTPClientDep,
    provider: OpenIDProviderDep,
    state: StateDep,
) -> KeySet:
    keys = cast(KeySet | None, getattr(state, "openid_provider_jwks", None))
    if keys is not None:
        return keys

    response = await http.get(str(provider.discovery.jwks_uri))
    state.openid_provider_jwks = KeySet.import_key_set(response.json())
    return state.openid_provider_jwks


async def get_oauth_client(
    provider: OpenIDProviderDep,
    request: Request,
    state: StateDep,
) -> OAuth2Client:
    client = cast(OAuth2Client | None, getattr(state, "oauth_client", None))
    if client is not None:
        return client

    print("Creating OAuth2 client")
    state.oauth_client = OAuth2Client(
        provider,
        redirect_uri=str(request.url_for("oauth_callback")),
    )
    return state.oauth_client


_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_token(
    keys: OpenIDProviderJWKsDep,
    authorization_header: Annotated[str, Depends(_oauth2_scheme)],
) -> Token:
    try:
        token = jwt.decode(authorization_header, keys)
    except JoseError as e:
        raise HTTPException(
            401,
            "Not authenticated",
            {"WWW-Authenticate": "Bearer"},
        ) from e

    return token


@cache
def get_settings() -> Settings:
    return Settings()


AsyncExitStackDep = Annotated[AsyncExitStack, Depends(get_async_exit_stack)]
CacheDep = Annotated[Cache, Depends(get_cache)]
HTTPClientDep = Annotated[httpx2.AsyncClient, Depends(get_http_client)]
OAuth2ClientDep = Annotated[OAuth2Client, Depends(get_oauth_client)]
OpenIDProviderDep = Annotated[OpenIDProvider, Depends(get_openid_provider)]
OpenIDProviderJWKsDep = Annotated[KeySet, Depends(get_openid_provider_jwks)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
StateDep = Annotated[State, Depends(get_state)]
TokenDep = Annotated[Token, Depends(get_token)]
