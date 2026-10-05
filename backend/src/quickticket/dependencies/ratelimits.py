import logging
import re
import time
from collections.abc import Sequence
from math import ceil
from re import Pattern
from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, Response
from limits import RateLimitItem, WindowStats, parse
from limits.aio.storage import MemoryStorage, Storage
from limits.aio.strategies import RateLimiter, SlidingWindowCounterRateLimiter

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

# https://limits.readthedocs.io/en/stable/quickstart.html#rate-limit-string-notation
RATELIMIT_ROUTES: dict[Pattern, RateLimitItem] = {
    re.compile(r"^/api/auth"): parse("20/minute"),
    re.compile(r"^/api"): parse("2000/hour"),
    re.compile(r"^/api"): parse("1000/10 minute"),
    re.compile(r"^/api"): parse("200/minute"),
    re.compile(r"^"): parse("20/second"),
}

log = logging.getLogger(__name__)


def get_limits_storage(state: StateDep) -> Storage:
    # TODO: create a quickticket Cache-compatible adapter to act as storage
    storage = cast(Storage | None, getattr(state, "limits_storage", None))
    if storage is not None:
        return storage

    state.limits_storage = MemoryStorage()
    return state.limits_storage


def get_limits_strategy(state: StateDep, storage: LimitsStorageDep) -> RateLimiter:
    strategy = cast(RateLimiter | None, getattr(state, "limits_strategy", None))
    if strategy is not None:
        return strategy

    state.strategy = SlidingWindowCounterRateLimiter(storage)
    return state.strategy


def get_request_identifier(request: Request, user: OptionalUserDep) -> tuple[str, ...]:
    # Maybe key the limit by account type, "user" vs. "admin" vs. "bot"
    if user is not None:
        return (str(user.id),)

    address = request.client
    if address is None:
        log.warning("Missing request.client for ratelimit identifier")
        return ("",)

    return (address.host,)


def get_request_limits(request: Request, user: OptionalUserDep) -> Sequence[RateLimitItem]:
    # Optionally adjust limit by account type
    # log.debug(
    #     "%s buckets: %s",
    #     request.url.path,
    #     ", ".join([repr(r.pattern) for r in RATELIMIT_ROUTES if r.match(request.url.path)]),
    # )
    return [limit for route, limit in RATELIMIT_ROUTES.items() if route.match(request.url.path)]


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
    return {
        "X-RateLimit-Limit": str(limit.amount),
        "X-RateLimit-Remaining": str(stats.remaining),
        "X-RateLimit-Reset": str(ceil(reset_time)),
        "X-RateLimit-Reset-After": str(ceil(reset_after)),
    }


LimitsRequestIdentifierDep = Annotated[Sequence[str], Depends(get_request_identifier)]
LimitsRequestLimitsDep = Annotated[Sequence[RateLimitItem], Depends(get_request_limits)]
LimitsStorageDep = Annotated[Storage, Depends(get_limits_storage)]
LimitsStrategyDep = Annotated[RateLimiter, Depends(get_limits_strategy)]
