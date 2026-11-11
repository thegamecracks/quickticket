from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx2 import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from quickticket.models import (
    Event,
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    Venue,
)
from tests.conftest import AuthController, DatasetLoader, assert_keyset_walk, isoformat


@pytest.mark.asyncio
async def test_get_events(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    await dataset_loader.load()

    response = await client.get("/api/events")
    assert response.status_code == 200
    data = response.json()

    # Should be limited to 10 events per request
    assert len(data["items"]) == min(10, len(dataset_loader.dataset.events))

    assert set(data) == {"items", "next", "total"}
    assert data["next"] is not None
    assert data["total"] == len(dataset_loader.dataset.events)

    ordered = sorted(
        dataset_loader.dataset.events,
        key=lambda event: event.created_at,
        reverse=True,
    )
    returned = ordered[:10]
    assert [event["id"] for event in data["items"]] == [str(event.id) for event in returned]

    async with make_session.begin() as session:
        for event in data["items"]:
            expected = await session.get(
                Event,
                UUID(event["id"]),
                options=[selectinload(Event.venue).selectinload(Venue.organization)],
            )
            assert expected is not None
            assert event == {
                "id": str(expected.id),
                "created_at": isoformat(expected.created_at),
                "display_name": expected.display_name,
                "description": expected.description,
                "theme": expected.theme,
                "thumbnail": None,
                "banner": None,
                "starts_at": isoformat(expected.starts_at),
                "ends_at": isoformat(expected.ends_at),
                "ticket_price": expected.ticket_price.model_dump(),
                "max_attendees": expected.max_attendees,
                "tickets": [],
                "venue": {
                    "id": str(expected.venue.id),
                    "created_at": isoformat(expected.venue.created_at),
                    "display_name": expected.venue.display_name,
                    "description": expected.venue.description,
                    "theme": expected.venue.theme,
                    "thumbnail": None,
                    "banner": None,
                    "location_name": expected.venue.location_name,
                    "location_coords": expected.venue.location_coords
                    and expected.venue.location_coords.model_dump(),
                    "organization": {
                        "id": str(expected.venue.organization.id),
                        "created_at": isoformat(expected.venue.organization.created_at),
                        "display_name": expected.venue.organization.display_name,
                    },
                },
            }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["organization_id", "expected_ids"],
    [
        (
            # Éclair Events
            UUID("2cbd7222-4fd3-4cef-9500-79746e76da89"),
            [
                UUID("ad1d67bd-d92c-41e8-8494-c943eaaac05a"),
                UUID("df7b2a4c-6647-43b7-88c7-17ddd2a43080"),
            ],
        ),
        (
            # Lopezs Event Planning and Decor
            UUID("8e21c0af-d7a0-4f06-940c-b23728ae59e1"),
            [
                UUID("5a1231e3-8e9a-4e87-9835-6db515975d7c"),
                UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
                UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
                UUID("21afa1a9-a4ed-4d2f-8908-93b743027fec"),
                UUID("0e161235-9c40-45e6-b4cd-022fd852f6e6"),
            ],
        ),
    ],
)
async def test_get_events_filtered_by_organization(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
    organization_id: UUID,
    expected_ids: list[UUID],
) -> None:
    await dataset_loader.load()

    response = await client.get("/api/events", params={"organization_id": str(organization_id)})
    assert response.status_code == 200
    data = response.json()

    assert [event["id"] for event in data["items"]] == [
        str(expected_id) for expected_id in expected_ids
    ]
    assert data["total"] == len(expected_ids)


@pytest.mark.asyncio
async def test_get_events_filtered_by_organization_with_no_events(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()

    # Golden Hour Gatherings has venues, but no events
    response = await client.get(
        "/api/events",
        params={"organization_id": "7092b056-4bec-4f3e-aec4-7f7e8f37b13d"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "next": None,
        "total": 0,
    }


@pytest.mark.asyncio
async def test_get_events_filtered_by_nonexistent_organization(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()

    response = await client.get(
        "/api/events",
        params={"organization_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "next": None,
        "total": 0,
    }


@pytest.mark.asyncio
async def test_get_events_empty_database(client: AsyncClient) -> None:
    response = await client.get("/api/events")
    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "next": None,
        "total": 0,
    }


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
async def test_get_events_before_matches_nothing(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()

    before = isoformat(datetime(2026, 1, 1, tzinfo=UTC))
    response = await client.get("/api/events", params={"before": before})
    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "next": None,
        "total": 0,
    }


@pytest.mark.asyncio
async def test_get_events_before_is_exclusive(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    ordered = sorted(dataset.events, key=lambda event: event.created_at, reverse=True)

    # Excluding the newest event leaves 11 events, of which the first page holds 10.
    response = await client.get("/api/events", params={"before": isoformat(ordered[0].created_at)})
    assert response.status_code == 200
    data = response.json()

    assert [event["id"] for event in data["items"]] == [str(event.id) for event in ordered[1:11]]
    assert data["next"] == isoformat(ordered[10].created_at)
    assert data["total"] == len(dataset.events) - 1


@pytest.mark.asyncio
async def test_get_events_before_and_organization_id(
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
            "before": isoformat(organization_events[2].created_at),
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert [event["id"] for event in data["items"]] == [
        str(event.id) for event in organization_events[3:]
    ]
    assert data["next"] is None
    assert data["total"] == 2


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
    ["params", "expected_loc", "expected_type"],
    [
        ({"next": "nope"}, ["query", "next"], "datetime_from_date_parsing"),
        ({"before": "nope"}, ["query", "before"], "datetime_from_date_parsing"),
        ({"next": "2026-10-20T00:00:00"}, ["query", "next"], "timezone_aware"),
        ({"before": "2026-10-20T00:00:00"}, ["query", "before"], "timezone_aware"),
        ({"limit": "0"}, ["query", "limit"], "greater_than"),
        ({"limit": "11"}, ["query", "limit"], "less_than_equal"),
        ({"limit": "abc"}, ["query", "limit"], "int_parsing"),
    ],
)
async def test_get_events_rejects_invalid_page_params(
    client: AsyncClient,
    params: dict[str, str],
    expected_loc: list[str],
    expected_type: str,
) -> None:
    response = await client.get("/api/events", params=params)
    assert response.status_code == 422

    errors = response.json()["detail"]
    assert any(error["loc"] == expected_loc and error["type"] == expected_type for error in errors)


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


@pytest.mark.asyncio
async def test_get_event(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset

    event = dataset.events[0]
    assert event.id == UUID("df7b2a4c-6647-43b7-88c7-17ddd2a43080")
    venue = next(v for v in dataset.venues if v.id == event.venue_id)
    assert venue.location_coords is not None
    organization = next(o for o in dataset.organizations if o.id == venue.organization_id)

    response = await client.get(f"/api/events/{event.id}")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 13
    assert data["id"] == str(event.id)
    assert data["created_at"] is not None
    assert data["display_name"] == event.display_name
    assert data["description"] == event.description
    assert data["theme"] == event.theme
    assert data["thumbnail"] is None
    assert data["banner"] is None
    assert datetime.fromisoformat(data["starts_at"]) == event.starts_at
    assert datetime.fromisoformat(data["ends_at"]) == event.ends_at
    assert data["ticket_price"] == event.ticket_price.model_dump()
    assert data["max_attendees"] == event.max_attendees
    assert data["tickets"] == []

    assert len(data["venue"]) == 10
    assert data["venue"]["id"] == str(venue.id)
    assert data["venue"]["created_at"] is not None
    assert data["venue"]["display_name"] == venue.display_name
    assert data["venue"]["description"] == venue.description
    assert data["venue"]["theme"] == venue.theme
    assert data["venue"]["thumbnail"] is None
    assert data["venue"]["banner"] is None
    assert data["venue"]["location_name"] == venue.location_name
    assert data["venue"]["location_coords"] == venue.location_coords.model_dump()

    assert len(data["venue"]["organization"]) == 3
    assert data["venue"]["organization"]["id"] == str(organization.id)
    assert data["venue"]["organization"]["created_at"] is not None
    assert data["venue"]["organization"]["display_name"] == organization.display_name


@pytest.mark.asyncio
async def test_get_event_not_found(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()

    response = await client.get("/api/events/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


@pytest.mark.asyncio
async def test_create_event(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    user = auth.user
    async with make_session.begin() as session:
        organization = Organization(display_name="Test Organization")
        member = OrganizationMember(
            organization_id=organization.id,
            account_id=user.id,
            permissions=OrganizationMemberPermissions.ADMINISTRATOR,
        )
        venue = Venue(
            organization_id=organization.id,
            display_name="Test Venue",
            description="A venue for testing.",
            theme="Sports",
            location_name="Test Stadium",
        )
        session.add_all([organization, member, venue])

    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=4)
    response = await client.post(
        "/api/events",
        json={
            "venue_id": str(venue.id),
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": isoformat(starts_at),
            "ends_at": isoformat(ends_at),
            "max_attendees": 500,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert response.headers["location"] == f"http://test/api/events/{data['id']}"

    assert len(data) == 13
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["display_name"] == "Test Hockey Tournament"
    assert data["description"] == "A mock hockey game, for testing."
    assert data["starts_at"] == isoformat(starts_at)
    assert data["ends_at"] == isoformat(ends_at)
    assert data["ticket_price"] == {"amount": 50, "currency": "CAD"}
    assert data["max_attendees"] == 500
    assert data["venue"]["id"] == str(venue.id)
    assert data["venue"]["display_name"] == "Test Venue"
    assert data["venue"]["organization"]["display_name"] == "Test Organization"

    # assert data["venue"]["description"] == "A venue for testing."
    # assert data["venue"]["theme"] == "Sports"
    # assert data["venue"]["location_name"] == "Test Stadium"
    # assert data["venue"]["location_coords"] == {"lat": 48.8584, "long": 2.2945}

    async with make_session.begin() as session:
        persisted = await session.get(Event, UUID(data["id"]))
        assert persisted is not None
        assert persisted.id == UUID(data["id"])


@pytest.mark.asyncio
async def test_create_event_no_permissions(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    user = auth.user
    async with make_session.begin() as session:
        organization = Organization(display_name="Test Organization")
        member = OrganizationMember(
            organization_id=organization.id,
            account_id=user.id,
            permissions=OrganizationMemberPermissions(0),
        )
        venue = Venue(
            organization_id=organization.id,
            display_name="Test Venue",
            description="A venue for testing.",
            theme="Sports",
            location_name="Test Stadium",
        )
        session.add_all([organization, member, venue])

    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=4)
    response = await client.post(
        "/api/events",
        json={
            "venue_id": str(venue.id),
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": isoformat(starts_at),
            "ends_at": isoformat(ends_at),
            "max_attendees": 500,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": f"Organization member ({organization.id}, {user.id}) missing permissions: ADMINISTRATOR"
    }


@pytest.mark.asyncio
async def test_create_event_no_venue(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    user = auth.user
    async with make_session.begin() as session:
        organization = Organization(display_name="Test Organization")
        member = OrganizationMember(
            organization_id=organization.id,
            account_id=user.id,
            permissions=OrganizationMemberPermissions.ADMINISTRATOR,
        )
        session.add_all([organization, member])

    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=4)
    response = await client.post(
        "/api/events",
        json={
            "venue_id": "00000000-0000-0000-0000-000000000000",
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": isoformat(starts_at),
            "ends_at": isoformat(ends_at),
            "max_attendees": 500,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Venue not found: 00000000-0000-0000-0000-000000000000"}


@pytest.mark.asyncio
async def test_create_event_rejects_max_attendees_below_minimum(
    client: AsyncClient,
) -> None:
    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=4)
    response = await client.post(
        "/api/events",
        json={
            "venue_id": "00000000-0000-0000-0000-000000000000",
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": isoformat(starts_at),
            "ends_at": isoformat(ends_at),
            "max_attendees": -1,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_event_rejects_max_attendees_above_maximum(
    client: AsyncClient,
) -> None:
    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=4)
    response = await client.post(
        "/api/events",
        json={
            "venue_id": "00000000-0000-0000-0000-000000000000",
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": isoformat(starts_at),
            "ends_at": isoformat(ends_at),
            "max_attendees": 10001,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_event_rejects_naive_datetimes(
    client: AsyncClient,
) -> None:
    starts_at = datetime.now() + timedelta(days=1)
    ends_at = starts_at
    response = await client.post(
        "/api/events",
        json={
            "venue_id": "00000000-0000-0000-0000-000000000000",
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": starts_at.isoformat(),
            "ends_at": ends_at.isoformat(),
            "max_attendees": 500,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "timezone_aware",
                "loc": ["body", "starts_at"],
                "msg": "Input should have timezone info",
                "input": starts_at.isoformat(),
            },
            {
                "type": "timezone_aware",
                "loc": ["body", "ends_at"],
                "msg": "Input should have timezone info",
                "input": ends_at.isoformat(),
            },
        ]
    }


@pytest.mark.asyncio
async def test_create_event_rejects_past_datetimes(
    client: AsyncClient,
) -> None:
    starts_at = datetime.now(UTC) - timedelta(days=1)
    ends_at = starts_at + timedelta(hours=4)
    response = await client.post(
        "/api/events",
        json={
            "venue_id": "00000000-0000-0000-0000-000000000000",
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": isoformat(starts_at),
            "ends_at": isoformat(ends_at),
            "max_attendees": 500,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "datetime_future",
                "loc": ["body", "starts_at"],
                "msg": "Input should be in the future",
                "input": isoformat(starts_at),
            },
            {
                "type": "datetime_future",
                "loc": ["body", "ends_at"],
                "msg": "Input should be in the future",
                "input": isoformat(ends_at),
            },
        ]
    }


@pytest.mark.asyncio
async def test_create_event_rejects_ends_at_before_starts_at(
    client: AsyncClient,
) -> None:
    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at - timedelta(hours=1)
    response = await client.post(
        "/api/events",
        json={
            "venue_id": "00000000-0000-0000-0000-000000000000",
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": isoformat(starts_at),
            "ends_at": isoformat(ends_at),
            "max_attendees": 500,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "value_error",
                "loc": ["body"],
                "msg": "Value error, starts_at must be before ends_at",
                "input": {
                    "venue_id": "00000000-0000-0000-0000-000000000000",
                    "display_name": "Test Hockey Tournament",
                    "description": "A mock hockey game, for testing.",
                    "theme": "Sports",
                    "starts_at": isoformat(starts_at),
                    "ends_at": isoformat(ends_at),
                    "max_attendees": 500,
                    "ticket_price": {"amount": 50, "currency": "CAD"},
                },
                "ctx": {"error": {}},
            }
        ]
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(["offset"], [(timedelta(),), (timedelta(minutes=59),)])
async def test_create_event_rejects_duration_below_minimum(
    client: AsyncClient,
    offset: timedelta,
) -> None:
    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + offset
    response = await client.post(
        "/api/events",
        json={
            "venue_id": "00000000-0000-0000-0000-000000000000",
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": isoformat(starts_at),
            "ends_at": isoformat(ends_at),
            "max_attendees": 500,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "value_error",
                "loc": ["body"],
                "msg": "Value error, Event duration must be between 1:00:00 and 7 days, 0:00:00",
                "input": {
                    "venue_id": "00000000-0000-0000-0000-000000000000",
                    "display_name": "Test Hockey Tournament",
                    "description": "A mock hockey game, for testing.",
                    "theme": "Sports",
                    "starts_at": isoformat(starts_at),
                    "ends_at": isoformat(ends_at),
                    "max_attendees": 500,
                    "ticket_price": {"amount": 50, "currency": "CAD"},
                },
                "ctx": {"error": {}},
            }
        ]
    }


@pytest.mark.asyncio
async def test_create_event_rejects_duration_above_maximum(
    client: AsyncClient,
) -> None:
    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + timedelta(days=8)
    response = await client.post(
        "/api/events",
        json={
            "venue_id": "00000000-0000-0000-0000-000000000000",
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": isoformat(starts_at),
            "ends_at": isoformat(ends_at),
            "max_attendees": 500,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "value_error",
                "loc": ["body"],
                "msg": "Value error, Event duration must be between 1:00:00 and 7 days, 0:00:00",
                "input": {
                    "venue_id": "00000000-0000-0000-0000-000000000000",
                    "display_name": "Test Hockey Tournament",
                    "description": "A mock hockey game, for testing.",
                    "theme": "Sports",
                    "starts_at": isoformat(starts_at),
                    "ends_at": isoformat(ends_at),
                    "max_attendees": 500,
                    "ticket_price": {"amount": 50, "currency": "CAD"},
                },
                "ctx": {"error": {}},
            }
        ]
    }
