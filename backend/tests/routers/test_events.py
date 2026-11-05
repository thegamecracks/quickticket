from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid7

import pytest
from httpx2 import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import (
    Event,
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    Venue,
)
from tests.conftest import AuthController, DatasetLoader


@pytest.mark.asyncio
async def test_get_events(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()

    response = await client.get("/api/events")
    assert response.status_code == 200
    data = response.json()

    # TODO: validate full payload? would be noisy with the descriptions though...
    event_ids = (
        UUID("ec2eb2b0-22d7-40c0-96f0-6f799227eba4"),
        UUID("97067d2e-7a1c-4451-ac3a-a8e974e1c6e3"),
        UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
        UUID("df8af935-6315-4a0f-9723-e4b031458a4d"),
        UUID("697102d3-6f53-4c93-b65b-f87a36a9b301"),
        UUID("5a1231e3-8e9a-4e87-9835-6db515975d7c"),
        UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
        UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
        UUID("21afa1a9-a4ed-4d2f-8908-93b743027fec"),
        UUID("0e161235-9c40-45e6-b4cd-022fd852f6e6"),
    )

    assert len(data["events"]) == len(event_ids)
    for i, event_id in enumerate(event_ids):
        assert data["events"][i]["id"] == str(event_id)


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

    response = await client.get(f"/api/events/{uuid7()}")
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
            "starts_at": starts_at.isoformat().replace("+00:00", "Z"),
            "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
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
    assert data["starts_at"] == starts_at.isoformat().replace("+00:00", "Z")
    assert data["ends_at"] == ends_at.isoformat().replace("+00:00", "Z")
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
            "starts_at": starts_at.isoformat().replace("+00:00", "Z"),
            "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
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

    venue_id = uuid7()  # random, no venue
    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=4)
    response = await client.post(
        "/api/events",
        json={
            "venue_id": str(venue_id),
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": starts_at.isoformat().replace("+00:00", "Z"),
            "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
            "max_attendees": 500,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": f"Venue not found: {venue_id}"}


@pytest.mark.asyncio
async def test_create_event_rejects_max_attendees_below_minimum(
    client: AsyncClient,
) -> None:
    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=4)
    response = await client.post(
        "/api/events",
        json={
            "venue_id": str(uuid7()),
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": starts_at.isoformat().replace("+00:00", "Z"),
            "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
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
            "venue_id": str(uuid7()),
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": starts_at.isoformat().replace("+00:00", "Z"),
            "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
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
            "venue_id": str(uuid7()),
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
            "venue_id": str(uuid7()),
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": starts_at.isoformat().replace("+00:00", "Z"),
            "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
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
                "input": starts_at.isoformat().replace("+00:00", "Z"),
            },
            {
                "type": "datetime_future",
                "loc": ["body", "ends_at"],
                "msg": "Input should be in the future",
                "input": ends_at.isoformat().replace("+00:00", "Z"),
            },
        ]
    }


@pytest.mark.asyncio
async def test_create_event_rejects_duration_below_minimum(
    client: AsyncClient,
) -> None:
    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + timedelta(minutes=59)
    response = await client.post(
        "/api/events",
        json={
            "venue_id": "00000000-0000-0000-0000-000000000000",
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            "starts_at": starts_at.isoformat().replace("+00:00", "Z"),
            "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
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
                    "starts_at": starts_at.isoformat().replace("+00:00", "Z"),
                    "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
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
            "starts_at": starts_at.isoformat().replace("+00:00", "Z"),
            "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
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
                    "starts_at": starts_at.isoformat().replace("+00:00", "Z"),
                    "ends_at": ends_at.isoformat().replace("+00:00", "Z"),
                    "max_attendees": 500,
                    "ticket_price": {"amount": 50, "currency": "CAD"},
                },
                "ctx": {"error": {}},
            }
        ]
    }
