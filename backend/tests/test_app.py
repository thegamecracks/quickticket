from collections.abc import AsyncGenerator
from http.cookies import SimpleCookie
from typing import NoReturn

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI, Response
from fastapi.responses import RedirectResponse
from httpx2 import ASGITransport, AsyncClient, Response as HTTPResponse

from quickticket.app import create_app_from_settings
from quickticket.dependencies.auth import get_user
from quickticket.errors import ForcedResponse
from quickticket.settings import FrontendSettings, LogSettings, OpenAPISettings, Settings


@pytest.fixture
def probe_app() -> FastAPI:
    """Create the real app with probe routes for exercising ``preserve_headers``."""
    settings = Settings(
        _env_file=None,
        frontend=FrontendSettings(builtin=False),
        log=LogSettings(debug=False, profiling=False),
        openapi=OpenAPISettings(url=None),
    )
    app = create_app_from_settings(settings)
    app.state.settings = settings
    # The app-wide rate limit dependency identifies anonymous clients by address,
    # but resolving a user would require OpenID settings these probes don't need.
    app.dependency_overrides[get_user] = lambda: None

    @app.post("/probe/cookies", response_model=None)
    async def cookies(response: Response) -> NoReturn:
        """Simulates a redirect after setting multiple cookies (login/logout)."""
        response.set_cookie("oauth-nonce", "nonce", max_age=1800, path="/api/auth")
        response.set_cookie("oauth-state", "state", max_age=1800, path="/api/auth")
        response.set_cookie("oauth-access-token", "access", max_age=300)
        raise ForcedResponse(RedirectResponse("/elsewhere", 303))

    @app.post("/probe/created", status_code=201)
    async def created(response: Response) -> dict[str, int]:
        """Simulates a create route returning plain data with a Location header."""
        response.headers["Location"] = "/probe/created/1"
        return {"id": 1}

    @app.post("/probe/plain-cookie")
    async def plain_cookie(response: Response) -> dict[str, int]:
        """Simulates refreshing a token before returning plain data."""
        response.set_cookie("oauth-access-token", "access", max_age=300)
        return {"id": 2}

    @app.post("/probe/returned-response")
    async def returned_response(response: Response) -> Response:
        """Simulates returning a response object that shares a header with ours."""
        response.headers["X-Shared"] = "same"
        response.headers["X-Temp-Only"] = "temp"
        return Response(headers={"X-Shared": "same"})

    return app


@pytest.fixture
async def middleware_client(probe_app: FastAPI) -> AsyncGenerator[AsyncClient]:
    async with (
        LifespanManager(probe_app),
        AsyncClient(
            transport=ASGITransport(probe_app),
            base_url="http://localhost",
        ) as client,
    ):
        yield client


def cookie_attributes(response: HTTPResponse) -> list[tuple[str, str, str, bool, bool]]:
    """Return (name, max-age, path, httponly, secure) for each Set-Cookie header."""
    return [
        (
            name,
            morsel["max-age"],
            morsel["path"],
            bool(morsel["httponly"]),
            bool(morsel["secure"]),
        )
        for header in response.headers.get_list("set-cookie")
        for name, morsel in SimpleCookie(header).items()
    ]


# Regression test for b7a99d4, which de-duplicated headers with
# `response.headers[k] = v` and thereby dropped all but one Set-Cookie header.
async def test_preserve_headers_keeps_multiple_set_cookie_headers(
    middleware_client: AsyncClient,
) -> None:
    response = await middleware_client.post("/probe/cookies")

    assert response.status_code == 303
    assert response.headers["location"] == "/elsewhere"
    # Cookie values are encrypted by the outermost middleware, so only their
    # attributes are observable here.
    assert cookie_attributes(response) == [
        ("oauth-nonce", "1800", "/api/auth", True, True),
        ("oauth-state", "1800", "/api/auth", True, True),
        ("oauth-access-token", "300", "/", True, True),
    ]


async def test_preserve_headers_does_not_duplicate_transferred_headers(
    middleware_client: AsyncClient,
) -> None:
    response = await middleware_client.post("/probe/created")

    assert response.status_code == 201
    assert response.headers.get_list("location") == ["/probe/created/1"]


async def test_preserve_headers_does_not_duplicate_transferred_cookies(
    middleware_client: AsyncClient,
) -> None:
    response = await middleware_client.post("/probe/plain-cookie")

    assert cookie_attributes(response) == [
        ("oauth-access-token", "300", "/", True, True),
    ]


async def test_preserve_headers_transfers_missing_headers_to_returned_response(
    middleware_client: AsyncClient,
) -> None:
    response = await middleware_client.post("/probe/returned-response")

    assert response.headers.get_list("x-shared") == ["same"]
    assert response.headers.get_list("x-temp-only") == ["temp"]
