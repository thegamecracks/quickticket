import pytest
from limits import WindowStats, parse
from starlette.requests import Request

from quickticket.dependencies.ratelimits import _create_ratelimit_headers, get_request_limits


def make_request(method: str, path: str, *, root_path: str = "") -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "path": f"{root_path}{path}",
            "root_path": root_path,
            "headers": [],
            "query_string": b"",
        },
    )


@pytest.mark.asyncio
async def test_get_request_limits_matches_root_path_relative_path() -> None:
    request = make_request("GET", "/api/foo", root_path="/prefix")

    limits = await get_request_limits(request, user=None)

    assert parse("2000/hour") in limits
    assert parse("1000/10 minute") in limits
    assert parse("200/minute") in limits
    assert parse("20/second") in limits


@pytest.mark.asyncio
async def test_general_api_limits_are_all_applied() -> None:
    limits = await get_request_limits(make_request("GET", "/api/foo"), user=None)

    assert parse("2000/hour") in limits
    assert parse("1000/10 minute") in limits
    assert parse("200/minute") in limits
    assert parse("20/second") in limits


@pytest.mark.asyncio
async def test_auth_limit_is_applied() -> None:
    limits = await get_request_limits(make_request("GET", "/api/auth/login"), user=None)

    assert parse("20/minute") in limits


def test_create_ratelimit_headers_includes_retry_after() -> None:
    headers = _create_ratelimit_headers(
        parse("10/minute"),
        WindowStats(reset_time=1_700_000_060.0, remaining=3),
        timestamp=1_700_000_000.0,
    )

    assert headers["Retry-After"] == "60"
    assert headers["X-RateLimit-Reset-After"] == "60"
