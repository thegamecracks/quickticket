import pytest
from limits import parse
from starlette.requests import Request

from quickticket.dependencies.ratelimits import get_request_limits


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
