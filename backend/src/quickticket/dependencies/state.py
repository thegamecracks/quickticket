import logging
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack
from functools import cache
from typing import Annotated, cast

import httpx2
from fastapi import Depends, FastAPI, Request
from fastapi.datastructures import State

from quickticket.settings import Settings

log = logging.getLogger(__name__)


@cache
def get_settings() -> Settings:
    return Settings()


def get_state(request: Request) -> State:
    return cast(FastAPI, request.app).state


def get_async_exit_stack(state: StateDep) -> AsyncExitStack:
    return cast(AsyncExitStack, state.stack)


async def get_http_client() -> AsyncIterator[httpx2.AsyncClient]:
    async with httpx2.AsyncClient() as client:
        yield client


AsyncExitStackDep = Annotated[AsyncExitStack, Depends(get_async_exit_stack)]
HTTPClientDep = Annotated[httpx2.AsyncClient, Depends(get_http_client)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
StateDep = Annotated[State, Depends(get_state)]
