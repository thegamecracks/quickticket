from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from httpx2 import AsyncClient

from quickticket.models import Event, Organization, Venue
from tests.conftest import DatasetLoader, assert_keyset_walk, isoformat

ENDPOINTS = ["/api/events", "/api/venues", "/api/organizations"]
"""The paginated endpoints sharing :class:`DateTimeFilterParams`."""

DEFAULT_LIMIT = 10


def ordered_collection(
    dataset_loader: DatasetLoader,
    url: str,
) -> Sequence[Event | Venue | Organization]:
    """Return the endpoint's collection ordered by creation time, newest first."""
    dataset = dataset_loader.dataset
    if url == "/api/events":
        return sorted(dataset.events, key=lambda event: event.created_at, reverse=True)
    if url == "/api/venues":
        return sorted(dataset.venues, key=lambda venue: venue.created_at, reverse=True)
    if url == "/api/organizations":
        return sorted(dataset.organizations, key=lambda org: org.created_at, reverse=True)
    assert False, f"Unknown endpoint: {url}"


def assert_page(
    data: dict[str, Any],
    expected: Sequence[Event | Venue | Organization],
    *,
    total: int,
) -> None:
    """Assert a single page of at most :data:`DEFAULT_LIMIT` items."""
    page = expected[:DEFAULT_LIMIT]
    assert [item["id"] for item in data["items"]] == [str(item.id) for item in page]
    # A full page continues at its last key; a partial page is the last page.
    next_key = isoformat(page[-1].created_at) if len(page) == DEFAULT_LIMIT else None
    assert data["next"] == next_key
    assert data["total"] == total


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ENDPOINTS)
async def test_after_filters_total(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
    url: str,
) -> None:
    await dataset_loader.load()
    ordered = ordered_collection(dataset_loader, url)

    # after is a filter: it excludes the oldest item.
    response = await client.get(url, params={"after": isoformat(ordered[-1].created_at)})
    assert response.status_code == 200

    assert_page(response.json(), ordered[:-1], total=len(ordered) - 1)


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ENDPOINTS)
async def test_after_is_exclusive(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
    url: str,
) -> None:
    await dataset_loader.load()
    ordered = ordered_collection(dataset_loader, url)

    # The item at the boundary is excluded, so it cannot appear on the page.
    response = await client.get(url, params={"after": isoformat(ordered[2].created_at)})
    assert response.status_code == 200
    data = response.json()

    assert [item["id"] for item in data["items"]] == [str(item.id) for item in ordered[:2]]
    assert data["total"] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ENDPOINTS)
async def test_after_newest_matches_nothing(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
    url: str,
) -> None:
    await dataset_loader.load()
    ordered = ordered_collection(dataset_loader, url)

    response = await client.get(url, params={"after": isoformat(ordered[0].created_at)})
    assert response.status_code == 200
    assert response.json() == {"items": [], "next": None, "total": 0}


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ENDPOINTS)
async def test_after_far_past_matches_everything(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
    url: str,
) -> None:
    await dataset_loader.load()
    ordered = ordered_collection(dataset_loader, url)

    after = isoformat(datetime(2000, 1, 1, tzinfo=UTC))
    response = await client.get(url, params={"after": after})
    assert response.status_code == 200

    assert_page(response.json(), ordered, total=len(ordered))


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ENDPOINTS)
async def test_after_and_before_window(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
    url: str,
) -> None:
    await dataset_loader.load()
    ordered = ordered_collection(dataset_loader, url)

    # Both bounds are exclusive, leaving the items strictly between them.
    response = await client.get(
        url,
        params={
            "after": isoformat(ordered[-2].created_at),
            "before": isoformat(ordered[1].created_at),
        },
    )
    assert response.status_code == 200
    data = response.json()

    expected = ordered[2:-2]
    assert [item["id"] for item in data["items"]] == [str(item.id) for item in expected]
    assert data["total"] == len(expected)


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ENDPOINTS)
@pytest.mark.parametrize(
    ["after_index", "before_index"],
    [
        # after is later than before
        (1, 3),
        # after equals before, and both bounds are exclusive
        (1, 1),
    ],
)
async def test_after_not_before_before_rejected(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
    url: str,
    after_index: int,
    before_index: int,
) -> None:
    await dataset_loader.load()
    ordered = ordered_collection(dataset_loader, url)

    response = await client.get(
        url,
        params={
            "after": isoformat(ordered[after_index].created_at),
            "before": isoformat(ordered[before_index].created_at),
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "value_error",
                "loc": ["query"],
                "msg": "Value error, after must be before before",
                "input": {
                    "after": isoformat(ordered[after_index].created_at),
                    "before": isoformat(ordered[before_index].created_at),
                },
                "ctx": {"error": {}},
            }
        ]
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("url", ENDPOINTS)
@pytest.mark.parametrize("limit", [1, 2])
async def test_after_pagination_walk(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
    url: str,
    limit: int,
) -> None:
    await dataset_loader.load()
    ordered = ordered_collection(dataset_loader, url)

    # The filter excludes the three oldest items, which span several pages.
    expected = ordered[:-3]
    await assert_keyset_walk(
        client,
        url,
        expected_ids=[item.id for item in expected],
        limit=limit,
        params={"after": isoformat(ordered[-3].created_at)},
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["params", "expected_loc", "expected_type"],
    [
        ({"next": "nope"}, ["query", "next"], "datetime_from_date_parsing"),
        ({"after": "nope"}, ["query", "after"], "datetime_from_date_parsing"),
        ({"before": "nope"}, ["query", "before"], "datetime_from_date_parsing"),
        ({"next": "2026-10-20T00:00:00"}, ["query", "next"], "timezone_aware"),
        ({"after": "2026-10-20T00:00:00"}, ["query", "after"], "timezone_aware"),
        ({"before": "2026-10-20T00:00:00"}, ["query", "before"], "timezone_aware"),
        ({"limit": "0"}, ["query", "limit"], "greater_than"),
        ({"limit": "11"}, ["query", "limit"], "less_than_equal"),
        ({"limit": "abc"}, ["query", "limit"], "int_parsing"),
    ],
)
@pytest.mark.parametrize("url", ENDPOINTS)
async def test_rejects_invalid_page_params(
    client: AsyncClient,
    url: str,
    params: dict[str, str],
    expected_loc: list[str],
    expected_type: str,
) -> None:
    response = await client.get(url, params=params)
    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(error["loc"] == expected_loc and error["type"] == expected_type for error in errors)


@pytest.mark.asyncio
async def test_get_events_after_and_organization_id(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset

    # Lopezs Event Planning and Decor
    organization_id = UUID("8e21c0af-d7a0-4f06-940c-b23728ae59e1")
    venue_organizations = {venue.id: venue.organization_id for venue in dataset.venues}
    organization_events = sorted(
        (
            event
            for event in dataset.events
            if venue_organizations[event.venue_id] == organization_id
        ),
        key=lambda event: event.created_at,
        reverse=True,
    )

    # The organization has five events; the filter excludes the three newest.
    response = await client.get(
        "/api/events",
        params={
            "organization_id": str(organization_id),
            "after": isoformat(organization_events[-3].created_at),
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert [event["id"] for event in data["items"]] == [
        str(event.id) for event in organization_events[:-3]
    ]
    assert data["next"] is None
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_get_events_after_and_next(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    ordered = ordered_collection(dataset_loader, "/api/events")

    response = await client.get(
        "/api/events",
        params={
            # after is a filter: it excludes the four oldest events and reduces total
            "after": isoformat(ordered[-4].created_at),
            # next paginates within the after-filtered set
            "next": isoformat(ordered[2].created_at),
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert [event["id"] for event in data["items"]] == [str(event.id) for event in ordered[3:-4]]
    assert data["next"] is None
    # next narrows the page, not the total dataset
    assert data["total"] == len(ordered) - 4


@pytest.mark.asyncio
async def test_get_events_next_key_is_last_created_at(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    """The current contract: next is the sort key of the page's last item."""
    await dataset_loader.load()

    response = await client.get("/api/events")
    assert response.status_code == 200
    data = response.json()

    assert len(data["items"]) == 10
    assert data["next"] == data["items"][-1]["created_at"]


@pytest.mark.asyncio
async def test_get_events_last_page_has_no_next(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    ordered = sorted(dataset.events, key=lambda event: event.created_at, reverse=True)

    # With 12 events and the default limit of 10, the second page holds the two
    # oldest events and is the last page.
    first = await client.get("/api/events")
    assert first.status_code == 200
    first_page = first.json()
    assert first_page["next"] is not None

    response = await client.get("/api/events", params={"next": first_page["next"]})
    assert response.status_code == 200
    data = response.json()

    assert [event["id"] for event in data["items"]] == [str(event.id) for event in ordered[10:]]
    assert data["next"] is None
    assert data["total"] == len(dataset.events)


@pytest.mark.asyncio
async def test_get_events_exact_multiple_ends_on_empty_page(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset

    # 12 events with a limit of 4, one empty page at end
    params = {"limit": 4}
    for expected_size in (4, 4, 4, 0):
        response = await client.get("/api/events", params=params)
        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == expected_size
        assert data["total"] == len(dataset.events)

        if expected_size > 0:
            assert data["next"] is not None
            params["next"] = data["next"]
        else:
            assert data["next"] is None


@pytest.mark.asyncio
async def test_get_events_next_is_exclusive(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    ordered = sorted(dataset.events, key=lambda event: event.created_at, reverse=True)

    response = await client.get("/api/events", params={"next": isoformat(ordered[3].created_at)})
    assert response.status_code == 200
    data = response.json()

    assert [event["id"] for event in data["items"]] == [str(event.id) for event in ordered[4:]]
    assert str(ordered[3].id) not in {event["id"] for event in data["items"]}
    assert data["next"] is None
    # next narrows the page, not the total dataset
    assert data["total"] == len(dataset.events)


@pytest.mark.asyncio
async def test_get_events_next_between_keys(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    ordered = sorted(dataset.events, key=lambda event: event.created_at, reverse=True)

    between = ordered[5].created_at - timedelta(days=1)
    response = await client.get("/api/events", params={"next": isoformat(between)})
    assert response.status_code == 200
    data = response.json()

    assert [event["id"] for event in data["items"]] == [str(event.id) for event in ordered[6:]]
    assert data["next"] is None
    assert data["total"] == len(dataset.events)


@pytest.mark.asyncio
async def test_get_events_next_oldest_key_returns_empty(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    ordered = sorted(dataset.events, key=lambda event: event.created_at, reverse=True)

    response = await client.get("/api/events", params={"next": isoformat(ordered[-1].created_at)})
    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "next": None,
        "total": len(dataset.events),
    }


@pytest.mark.asyncio
async def test_get_events_before_and_next(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    ordered = sorted(dataset.events, key=lambda event: event.created_at, reverse=True)

    response = await client.get(
        "/api/events",
        params={
            # before is a filter: it excludes the newest event and reduces total
            "before": isoformat(ordered[0].created_at),
            # next paginates within the before-filtered set
            "next": isoformat(ordered[2].created_at),
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert [event["id"] for event in data["items"]] == [str(event.id) for event in ordered[3:]]
    assert data["next"] is None
    assert data["total"] == len(dataset.events) - 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["organization_id", "expected_total"],
    [
        # No filter
        (None, 12),
        # Éclair Events, whose events fit in one page
        (UUID("2cbd7222-4fd3-4cef-9500-79746e76da89"), 2),
        # Lopezs Event Planning and Decor, whose events span multiple pages
        (UUID("8e21c0af-d7a0-4f06-940c-b23728ae59e1"), 5),
    ],
)
@pytest.mark.parametrize("limit", [10, 1])
async def test_get_events_pagination_walk(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
    organization_id: UUID | None,
    expected_total: int,
    limit: int,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    venue_organizations = {venue.id: venue.organization_id for venue in dataset.venues}
    expected = sorted(
        (
            event
            for event in dataset.events
            if organization_id is None or venue_organizations[event.venue_id] == organization_id
        ),
        key=lambda event: event.created_at,
        reverse=True,
    )

    params = {}
    if organization_id is not None:
        params["organization_id"] = str(organization_id)

    assert len(expected) == expected_total
    await assert_keyset_walk(
        client,
        "/api/events",
        expected_ids=[event.id for event in expected],
        limit=limit,
        params=params,
    )


@pytest.mark.asyncio
async def test_get_events_pagination_walk_with_before(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset

    # Lopezs Event Planning and Decor
    organization_id = UUID("8e21c0af-d7a0-4f06-940c-b23728ae59e1")
    venue_organizations = {venue.id: venue.organization_id for venue in dataset.venues}
    organization_events = sorted(
        (
            event
            for event in dataset.events
            if venue_organizations[event.venue_id] == organization_id
        ),
        key=lambda event: event.created_at,
        reverse=True,
    )

    # The filter excludes the newest event, leaving four across three pages.
    await assert_keyset_walk(
        client,
        "/api/events",
        expected_ids=[event.id for event in organization_events[1:]],
        limit=2,
        params={
            "organization_id": str(organization_id),
            "before": isoformat(organization_events[0].created_at),
        },
    )
