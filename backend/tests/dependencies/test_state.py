from contextlib import AsyncExitStack, asynccontextmanager
from unittest.mock import MagicMock

import httpx2
import pytest
from fastapi import FastAPI, Request
from fastapi.datastructures import State

from quickticket.dependencies.state import (
    get_async_exit_stack,
    get_http_client,
    get_settings,
    get_state,
)


@pytest.mark.asyncio
async def test_get_state(app: FastAPI, state: State) -> None:
    request = Request({"type": "http", "app": app})
    assert await get_state(request) is state


@pytest.mark.asyncio
async def test_get_settings_caches_settings(
    monkeypatch: pytest.MonkeyPatch,
    state: State,
) -> None:
    stub = object()
    settings_mock = MagicMock(return_value=stub)
    monkeypatch.setattr("quickticket.dependencies.state.Settings", settings_mock)

    settings_1 = await get_settings(state)
    settings_2 = await get_settings(state)

    assert settings_1 is stub
    assert settings_2 is stub
    settings_mock.assert_called_once()


@pytest.mark.asyncio
async def test_get_async_exit_stack(app: FastAPI, stack: AsyncExitStack) -> None:
    assert await get_async_exit_stack(app.state) is stack


@pytest.mark.asyncio
async def test_get_http_client_closes_client() -> None:
    async with asynccontextmanager(get_http_client)() as client:
        assert isinstance(client, httpx2.AsyncClient)
        assert not client.is_closed

    assert client.is_closed
