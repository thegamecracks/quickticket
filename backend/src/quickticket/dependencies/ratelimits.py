import logging
import re
import time
from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil
from re import Pattern
from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, Response
from limits import RateLimitItem, WindowStats, parse
from limits.aio.storage import MemoryStorage, Storage
from limits.aio.strategies import RateLimiter, SlidingWindowCounterRateLimiter
from starlette.routing import get_route_path

from quickticket.dependencies.auth import OptionalUserDep
from quickticket.dependencies.state import StateDep

__all__ = (
    "LimitsRequestIdentifierDep",
    "LimitsRequestLimitsDep",
    "LimitsStorageDep",
    "LimitsStrategyDep",
    "apply_request_limit",
    "get_limits_storage",
    "get_limits_strategy",
    "get_request_limits",
)


@dataclass(frozen=True, kw_only=True)
class RateLimitRule:
    """A rate limit rule matching a request method and path."""

    path: Pattern[str]
    limits: tuple[RateLimitItem, ...]
    methods: frozenset[str] | None = None
    """The HTTP methods this rule applies to, or None for all methods."""

    def matches(self, method: str, path: str) -> bool:
        if self.methods is not None and method not in self.methods:
            return False
        return self.path.match(path) is not None


# Image routes are generated as /api/<entity>/<id>/<kind>.
IMAGE_PATH_PATTERN = re.compile(r"^/api/[^/]+/[^/]+/(banner|thumbnail)$")

# https://limits.readthedocs.io/en/stable/quickstart.html#rate-limit-string-notation
RATELIMIT_RULES: tuple[RateLimitRule, ...] = (
    RateLimitRule(
        path=re.compile(r"^/api/auth"),
        limits=(parse("20/minute"),),
    ),
    RateLimitRule(
        path=IMAGE_PATH_PATTERN,
        methods=frozenset({"PUT"}),
        limits=(parse("10/minute"), parse("100/hour")),
    ),
    RateLimitRule(
        path=IMAGE_PATH_PATTERN,
        methods=frozenset({"DELETE"}),
        limits=(parse("30/minute"), parse("300/hour")),
    ),
    RateLimitRule(
        path=re.compile(r"^/api"),
        limits=(parse("2000/hour"), parse("1000/10 minute"), parse("200/minute")),
    ),
    RateLimitRule(
        path=re.compile(r"^"),
        limits=(parse("20/second"),),
    ),
)

log = logging.getLogger(__name__)


async def get_limits_storage(state: StateDep) -> Storage:
    # TODO: create a quickticket Cache-compatible adapter to act as storage
    storage = cast(Storage | None, getattr(state, "limits_storage", None))
    if storage is not None:
        return storage

    state.limits_storage = MemoryStorage()
    return state.limits_storage


async def get_limits_strategy(state: StateDep, storage: LimitsStorageDep) -> RateLimiter:
    strategy = cast(RateLimiter | None, getattr(state, "limits_strategy", None))
    if strategy is not None:
        return strategy

    state.strategy = SlidingWindowCounterRateLimiter(storage)
    return state.strategy


async def get_request_identifier(request: Request, user: OptionalUserDep) -> tuple[str, ...]:
    # Maybe key the limit by account type, "user" vs. "admin" vs. "bot"
    if user is not None:
        return (str(user.id),)

    address = request.client
    if address is None:
        log.warning("Missing request.client for ratelimit identifier")
        return ("",)

    # TODO: normalize IPv6 addresses to their /48 subnet so that addresses
    # within the same subnet share a bucket.
    return (address.host,)


async def get_request_limits(request: Request, user: OptionalUserDep) -> Sequence[RateLimitItem]:
    # Optionally adjust limit by account type
    path = get_route_path(request.scope)
    return [
        limit
        for rule in RATELIMIT_RULES
        if rule.matches(request.method, path)
        for limit in rule.limits
    ]


async def apply_request_limit(
    strategy: LimitsStrategyDep,
    limits: LimitsRequestLimitsDep,
    identifier: LimitsRequestIdentifierDep,
    response: Response,
) -> dict[str, str]:
    if not limits:
        return {}

    evaluated: list[tuple[RateLimitItem, WindowStats]] = []
    failed: tuple[RateLimitItem, WindowStats] | None = None
    for limit in limits:
        stats = await strategy.get_window_stats(limit, *identifier)
        pair = (limit, stats)
        evaluated.append(pair)

        if not await strategy.hit(limit, *identifier):
            failed = pair
            break

    if failed is not None:
        timestamp = time.time()
        reset_after = failed[1].reset_time - timestamp
        headers = _create_ratelimit_headers(failed[0], failed[1], timestamp)
        raise HTTPException(
            429,
            f"You are currently ratelimited for {reset_after:.1f} seconds.",
            headers=headers,
        )

    # Return only the lowest ratelimit
    limit, stats = min(evaluated, key=lambda t: (t[1].remaining, t[0].amount))
    headers = _create_ratelimit_headers(limit, stats, time.time())
    response.headers.update(headers)
    return headers


def _create_ratelimit_headers(
    limit: RateLimitItem,
    stats: WindowStats,
    timestamp: float,
) -> dict[str, str]:
    reset_time = stats.reset_time
    reset_after = max(0, reset_time - timestamp)
    retry_after = ceil(reset_after)
    return {
        "X-RateLimit-Limit": str(limit.amount),
        "X-RateLimit-Remaining": str(stats.remaining),
        "X-RateLimit-Reset": str(ceil(reset_time)),
        "X-RateLimit-Reset-After": str(retry_after),
        "Retry-After": str(retry_after),
    }


LimitsRequestIdentifierDep = Annotated[Sequence[str], Depends(get_request_identifier)]
LimitsRequestLimitsDep = Annotated[Sequence[RateLimitItem], Depends(get_request_limits)]
LimitsStorageDep = Annotated[Storage, Depends(get_limits_storage)]
LimitsStrategyDep = Annotated[RateLimiter, Depends(get_limits_strategy)]
