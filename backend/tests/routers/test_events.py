from datetime import datetime
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import (
    Event,
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    User,
    Venue,
)
from tests.conftest import AuthController, DatasetLoader


@pytest.mark.asyncio
async def test_get_events(
    app: FastAPI,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()

    client = TestClient(app)
    response = client.get("/api/events")
    response.raise_for_status()
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
async def test_create_event(
    app: FastAPI,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    async with make_session() as session, session.begin():
        auth.user = user = User(
            display_name="Display Name",
            first_name="First",
            last_name="Last",
            email="user@example.com",
        )
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
        session.add_all([user, organization, member, venue])

    client = TestClient(app)
    response = client.post(
        "/api/events",
        json={
            "venue_id": str(venue.id),
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            # should display jan 1st, 2027, 6-10pm
            "starts_at": datetime(2027, 1, 1, 18, 0).isoformat(),
            "ends_at": datetime(2027, 1, 1, 22, 0).isoformat(),
            "max_attendees": 500,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    response.raise_for_status()
    data = response.json()

    assert len(data) == 13
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["display_name"] == "Test Hockey Tournament"
    assert data["description"] == "A mock hockey game, for testing."
    assert data["starts_at"] == datetime(2027, 1, 1, 18, 0).isoformat()
    assert data["ends_at"] == datetime(2027, 1, 1, 22, 0).isoformat()
    assert data["ticket_price"] == {"amount": 50, "currency": "CAD"}
    assert data["max_attendees"] == 500
    assert data["venue"]["id"] == str(venue.id)
    assert data["venue"]["display_name"] == "Test Venue"
    assert data["venue"]["organization"]["display_name"] == "Test Organization"

    # assert data["venue"]["description"] == "A venue for testing."
    # assert data["venue"]["theme"] == "Sports"
    # assert data["venue"]["location_name"] == "Test Stadium"
    # assert data["venue"]["location_coords"] == {"lat": 48.8584, "long": 2.2945}

    async with make_session() as session, session.begin():
        persisted = await session.get(Event, UUID(data["id"]))
        assert persisted is not None
        assert persisted.id == UUID(data["id"])


@pytest.mark.asyncio
async def test_create_event_no_permissions(
    app: FastAPI,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    async with make_session() as session, session.begin():
        auth.user = user = User(
            display_name="Display Name",
            first_name="First",
            last_name="Last",
            email="user@example.com",
        )
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
        session.add_all([user, organization, member, venue])

    client = TestClient(app)
    response = client.post(
        "/api/events",
        json={
            "venue_id": str(venue.id),
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            # should display jan 1st, 2027, 6-10pm
            "starts_at": datetime(2027, 1, 1, 18, 0).isoformat(),
            "ends_at": datetime(2027, 1, 1, 22, 0).isoformat(),
            "max_attendees": 500,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            f"Organization member ((UUID('{organization.id}'), UUID('{user.id}'))) "
            f"missing permissions: ADMINISTRATOR"
        )
    }


@pytest.mark.asyncio
async def test_create_event_no_venue(
    app: FastAPI,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    async with make_session() as session, session.begin():
        auth.user = user = User(
            display_name="Display Name",
            first_name="First",
            last_name="Last",
            email="user@example.com",
        )
        organization = Organization(display_name="Test Organization")
        member = OrganizationMember(
            organization_id=organization.id,
            account_id=user.id,
            permissions=OrganizationMemberPermissions.ADMINISTRATOR,
        )
        session.add_all([user, organization, member])

    venue_id = uuid4()  # random, no venue
    client = TestClient(app)
    response = client.post(
        "/api/events",
        json={
            "venue_id": str(venue_id),
            "display_name": "Test Hockey Tournament",
            "description": "A mock hockey game, for testing.",
            "theme": "Sports",
            # should display jan 1st, 2027, 6-10pm
            "starts_at": datetime(2027, 1, 1, 18, 0).isoformat(),
            "ends_at": datetime(2027, 1, 1, 22, 0).isoformat(),
            "max_attendees": 500,
            "ticket_price": {"amount": 50, "currency": "CAD"},
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": f"Venue not found: {venue_id}"}
