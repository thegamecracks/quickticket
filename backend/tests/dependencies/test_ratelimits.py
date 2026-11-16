import re
from collections.abc import Sequence

import pytest
from limits import RateLimitItem, WindowStats, parse
from starlette.requests import Request

from quickticket.dependencies.ratelimits import (
    RateLimitRule,
    _create_ratelimit_headers,
    get_ratelimit_rules,
    get_request_limits,
)

ENTITY_ID = "00000000-0000-0000-0000-000000000000"

# Test-owned rules, so the matching assertions don't restate production values.
MATCHING_RULES = (
    RateLimitRule(
        path=re.compile(r"^/api/widgets$"),
        methods=frozenset({"PUT"}),
        limits=(parse("1/minute"),),
    ),
    RateLimitRule(path=re.compile(r"^/api"), limits=(parse("2/minute"),)),
    RateLimitRule(path=re.compile(r"^"), limits=(parse("3/minute"),)),
)

GENERAL_LIMITS = {
    parse("2000/hour"),
    parse("1000/10 minute"),
    parse("200/minute"),
    parse("20/second"),
}


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


async def get_limits(
    method: str,
    path: str,
    *,
    root_path: str = "",
    rules: Sequence[RateLimitRule] = MATCHING_RULES,
) -> list[RateLimitItem]:
    limits = await get_request_limits(
        make_request(method, path, root_path=root_path),
        user=None,
        rules=rules,
    )
    return list(limits)


async def test_rules_accumulate_in_declaration_order() -> None:
    assert await get_limits("GET", "/api/widgets") == [parse("2/minute"), parse("3/minute")]


async def test_method_filter_selects_rules() -> None:
    assert await get_limits("PUT", "/api/widgets") == [
        parse("1/minute"),
        parse("2/minute"),
        parse("3/minute"),
    ]
    assert await get_limits("GET", "/api/widgets") == [parse("2/minute"), parse("3/minute")]


async def test_root_path_is_stripped_before_matching() -> None:
    assert await get_limits("GET", "/api/widgets", root_path="/prefix") == [
        parse("2/minute"),
        parse("3/minute"),
    ]


async def test_rule_path_must_match_the_whole_route() -> None:
    assert await get_limits("PUT", "/api/widgets/extra") == [parse("2/minute"), parse("3/minute")]


def test_create_ratelimit_headers_includes_retry_after() -> None:
    headers = _create_ratelimit_headers(
        parse("10/minute"),
        WindowStats(reset_time=1_700_000_060.0, remaining=3),
        timestamp=1_700_000_000.0,
    )

    assert headers["Retry-After"] == "60"
    assert headers["X-RateLimit-Reset-After"] == "60"


@pytest.mark.parametrize(
    ("method", "path", "expected"),
    [
        (
            "PUT",
            f"/api/venues/{ENTITY_ID}/banner",
            {parse("10/minute"), parse("100/hour")},
        ),
        (
            "PUT",
            f"/api/events/{ENTITY_ID}/thumbnail",
            {parse("10/minute"), parse("100/hour")},
        ),
        (
            "DELETE",
            f"/api/venues/{ENTITY_ID}/banner",
            {parse("30/minute"), parse("300/hour")},
        ),
        ("GET", "/api/auth/login", {parse("20/minute")}),
        ("GET", "/api/events", set()),
    ],
)
async def test_production_rules_add_limits_for_route(
    method: str,
    path: str,
    expected: set[RateLimitItem],
) -> None:
    limits = set(await get_limits(method, path, rules=await get_ratelimit_rules()))

    assert limits - GENERAL_LIMITS == expected
    assert limits >= GENERAL_LIMITS
