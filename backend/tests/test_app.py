from collections.abc import AsyncGenerator
from typing import NoReturn

import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI, Response
from fastapi.responses import RedirectResponse
from httpx2 import ASGITransport, AsyncClient
from starlette.middleware.base import BaseHTTPMiddleware

from quickticket.app import handle_forced_response, preserve_headers, store_response_object
from quickticket.errors import ForcedResponse


def create_middleware_test_app() -> FastAPI:
    """Create an app that wires ``preserve_headers`` like the real app does."""
    app = FastAPI(dependencies=[Depends(store_response_object)])
    app.add_middleware(BaseHTTPMiddleware, dispatch=preserve_headers)
    app.add_exception_handler(ForcedResponse, handle_forced_response)  # ty: ignore[invalid-argument-type]

    @app.post("/cookies", response_model=None)
    async def cookies(response: Response) -> NoReturn:
        """Simulates a redirect after setting multiple cookies (login/logout)."""
        response.set_cookie("oauth-nonce", "nonce", max_age=1800, path="/api/auth")
        response.set_cookie("oauth-state", "state", max_age=1800, path="/api/auth")
        response.set_cookie("oauth-access-token", "access", max_age=300)
        raise ForcedResponse(RedirectResponse("/elsewhere", 303))

    @app.post("/created", status_code=201)
    async def created(response: Response) -> dict[str, int]:
        """Simulates a create route returning plain data with a Location header."""
        response.headers["Location"] = "http://test/created/1"
        return {"id": 1}

    @app.post("/plain-cookie")
    async def plain_cookie(response: Response) -> dict[str, int]:
        """Simulates refreshing a token before returning plain data."""
        response.set_cookie("oauth-access-token", "access", max_age=300)
        return {"id": 2}

    @app.post("/returned-response")
    async def returned_response(response: Response) -> Response:
        """Simulates returning a response object that shares a header with ours."""
        response.headers["X-Shared"] = "same"
        response.headers["X-Temp-Only"] = "temp"
        return Response(headers={"X-Shared": "same"})

    return app


@pytest_asyncio.fixture
async def middleware_client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(create_middleware_test_app()),
        base_url="http://test",
    ) as client:
        yield client


# Regression test for b7a99d4, which de-duplicated headers with
# `response.headers[k] = v` and thereby dropped all but one Set-Cookie header.
@pytest.mark.asyncio
async def test_preserve_headers_keeps_multiple_set_cookie_headers(
    middleware_client: AsyncClient,
) -> None:
    response = await middleware_client.post("/cookies")

    assert response.status_code == 303
    assert response.headers["location"] == "/elsewhere"
    assert response.headers.get_list("set-cookie") == [
        "oauth-nonce=nonce; Max-Age=1800; Path=/api/auth; SameSite=lax",
        "oauth-state=state; Max-Age=1800; Path=/api/auth; SameSite=lax",
        "oauth-access-token=access; Max-Age=300; Path=/; SameSite=lax",
    ]


@pytest.mark.asyncio
async def test_preserve_headers_does_not_duplicate_transferred_headers(
    middleware_client: AsyncClient,
) -> None:
    response = await middleware_client.post("/created")

    assert response.status_code == 201
    assert response.headers.get_list("location") == ["http://test/created/1"]


@pytest.mark.asyncio
async def test_preserve_headers_does_not_duplicate_transferred_cookies(
    middleware_client: AsyncClient,
) -> None:
    response = await middleware_client.post("/plain-cookie")

    assert response.headers.get_list("set-cookie") == [
        "oauth-access-token=access; Max-Age=300; Path=/; SameSite=lax",
    ]


@pytest.mark.asyncio
async def test_preserve_headers_transfers_missing_headers_to_returned_response(
    middleware_client: AsyncClient,
) -> None:
    response = await middleware_client.post("/returned-response")

    assert response.headers.get_list("x-shared") == ["same"]
    assert response.headers.get_list("x-temp-only") == ["temp"]
