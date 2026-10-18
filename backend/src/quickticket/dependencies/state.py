import logging
from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack
from typing import Annotated, cast

import httpx2
from fastapi import Depends, FastAPI, Request
from fastapi.datastructures import State

from quickticket.settings import Settings

__all__ = (
    "AsyncExitStackDep",
    "HTTPClientDep",
    "SettingsDep",
    "StateDep",
    "get_async_exit_stack",
    "get_http_client",
    "get_settings",
    "get_state",
)

log = logging.getLogger(__name__)


async def get_state(request: Request) -> State:
    return cast(FastAPI, request.app).state


async def get_settings(state: StateDep) -> Settings:
    settings = cast(Settings | None, getattr(state, "settings", None))
    if settings is not None:
        return settings

    state.settings = Settings()
    return state.settings


async def get_async_exit_stack(state: StateDep) -> AsyncExitStack:
    return cast(AsyncExitStack, state.stack)  # set in lifespan function


async def get_http_client() -> AsyncGenerator[httpx2.AsyncClient]:
    async with httpx2.AsyncClient() as client:
        yield client


AsyncExitStackDep = Annotated[AsyncExitStack, Depends(get_async_exit_stack)]
HTTPClientDep = Annotated[httpx2.AsyncClient, Depends(get_http_client)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
StateDep = Annotated[State, Depends(get_state)]
