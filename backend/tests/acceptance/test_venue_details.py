"""Acceptance tests for user story #44: an attendee can see venue details.

Covers GitHub issue #94. Each test is one scenario from the story:

- full details (venue name and location)
- virtual venue (location name only, no coordinates)
- zero events
- one or more active events
- past (already-ended) events
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx2 import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import Event, VenueID
from tests.acceptance.helpers import make_administrator, venue_body
from tests.conftest import AuthController, DatasetLoader, isoformat


@pytest.mark.asyncio
async def test_attendee_sees_venue_name_and_location(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    auth.user = None
    venue = next(
        item
        for item in dataset_loader.dataset.venues
        if item.location_coords is not None and item.location_name and item.description
    )
    organization = next(
        item for item in dataset_loader.dataset.organizations if item.id == venue.organization_id
    )

    response = await client.get(f"/api/venues/{venue.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == venue.display_name
    assert data["description"] == venue.description
    assert data["location_name"] == venue.location_name
    assert venue.location_coords is not None
    assert data["location_coords"] == venue.location_coords.model_dump()
    assert data["organization"]["id"] == str(organization.id)
    assert data["organization"]["display_name"] == organization.display_name


@pytest.mark.asyncio
async def test_attendee_sees_virtual_venue_without_coordinates(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    organization = await make_administrator(make_session, auth.user)
    created = await client.post(
        "/api/venues",
        json=venue_body(
            organization.id,
            display_name="Zoom Room",
            description="An online listening session.",
            theme="Music",
            location_name="Zoom",
            location_coords=None,
        ),
    )
    assert created.status_code == 201
    venue_id = created.json()["id"]
    auth.user = None

    response = await client.get(f"/api/venues/{venue_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Zoom Room"
    assert data["location_name"] == "Zoom"
    assert data["location_coords"] is None


@pytest.mark.asyncio
async def test_attendee_sees_venue_with_zero_events(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    auth.user = None
    used_venue_ids = {event.venue_id for event in dataset_loader.dataset.events}
    venue = next(item for item in dataset_loader.dataset.venues if item.id not in used_venue_ids)

    response = await client.get(f"/api/venues/{venue.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == venue.display_name
    assert data["location_name"] == venue.location_name
    assert data["events"] == []


@pytest.mark.asyncio
async def test_attendee_sees_active_events_at_a_venue(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    organization = await make_administrator(make_session, auth.user)
    created = await client.post("/api/venues", json=venue_body(organization.id))
    assert created.status_code == 201
    venue_id = VenueID(UUID(created.json()["id"]))
    starts_at = datetime.now(UTC) + timedelta(days=2)
    ends_at = starts_at + timedelta(hours=3)
    async with make_session.begin() as session:
        event = Event(
            venue_id=venue_id,
            display_name="Friday Night Session",
            description="An upcoming show.",
            theme="Music",
            starts_at=starts_at,
            ends_at=ends_at,
        )
        session.add(event)
    auth.user = None

    response = await client.get(f"/api/venues/{venue_id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 1
    listed = data["events"][0]
    assert listed["id"] == str(event.id)
    assert listed["display_name"] == "Friday Night Session"
    assert listed["starts_at"] == isoformat(starts_at)
    assert listed["ends_at"] == isoformat(ends_at)
    assert datetime.fromisoformat(listed["ends_at"]) > datetime.now(UTC)


@pytest.mark.asyncio
async def test_attendee_sees_past_events_at_a_venue(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    organization = await make_administrator(make_session, auth.user)
    created = await client.post(
        "/api/venues",
        json=venue_body(organization.id, display_name="Archive Hall"),
    )
    assert created.status_code == 201
    venue_id = VenueID(UUID(created.json()["id"]))
    starts_at = datetime.now(UTC) - timedelta(days=10)
    ends_at = starts_at + timedelta(hours=2)
    async with make_session.begin() as session:
        event = Event(
            venue_id=venue_id,
            display_name="October Listening Party",
            description="A show that already ended.",
            theme="Music",
            starts_at=starts_at,
            ends_at=ends_at,
        )
        session.add(event)
    auth.user = None

    response = await client.get(f"/api/venues/{venue_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "Archive Hall"
    assert len(data["events"]) == 1
    listed = data["events"][0]
    assert listed["id"] == str(event.id)
    assert listed["display_name"] == "October Listening Party"
    assert listed["starts_at"] == isoformat(starts_at)
    assert listed["ends_at"] == isoformat(ends_at)
    assert datetime.fromisoformat(listed["ends_at"]) < datetime.now(UTC)


@pytest.mark.asyncio
async def test_attendee_gets_not_found_for_unknown_venue(
    client: AsyncClient,
    auth: AuthController,
) -> None:
    auth.user = None

    response = await client.get("/api/venues/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


@pytest.mark.asyncio
async def test_active_and_past_events_are_both_listed(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    organization = await make_administrator(make_session, auth.user)
    created = await client.post("/api/venues", json=venue_body(organization.id))
    assert created.status_code == 201
    venue_id = VenueID(UUID(created.json()["id"]))
    now = datetime.now(UTC)
    async with make_session.begin() as session:
        past = Event(
            venue_id=venue_id,
            display_name="Last Month",
            description="Ended.",
            theme="Music",
            starts_at=now - timedelta(days=30),
            ends_at=now - timedelta(days=30, hours=-2),
        )
        active = Event(
            venue_id=venue_id,
            display_name="Next Week",
            description="Not ended.",
            theme="Music",
            starts_at=now + timedelta(days=7),
            ends_at=now + timedelta(days=7, hours=2),
        )
        session.add_all([past, active])
    auth.user = None

    response = await client.get(f"/api/venues/{venue_id}")

    assert response.status_code == 200
    events = {item["display_name"]: item for item in response.json()["events"]}
    assert set(events) == {"Last Month", "Next Week"}
    assert datetime.fromisoformat(events["Last Month"]["ends_at"]) < now
    assert datetime.fromisoformat(events["Next Week"]["ends_at"]) > now


@pytest.mark.asyncio
async def test_created_venue_round_trips_through_details(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    """A venue saved by an organizer is the venue an attendee later opens."""
    assert auth.user is not None
    organization = await make_administrator(make_session, auth.user)
    created = await client.post("/api/venues", json=venue_body(organization.id))
    assert created.status_code == 201
    venue_id = created.json()["id"]
    auth.user = None

    response = await client.get(f"/api/venues/{venue_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == venue_id
    assert data["display_name"] == "Harbour Hall"
    assert data["location_name"] == "88 Granville St., Toronto"
    assert data["location_coords"] == {"lat": 43.6532, "long": -79.3832}
    assert data["events"] == []
