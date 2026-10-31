import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import (
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    User,
    Venue,
)
from quickticket.routers.venues import VENUE_LIMIT
from tests.conftest import AuthController


@pytest.mark.asyncio
async def test_create_venue(
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

    client = TestClient(app)
    response = client.post(
        "/api/venues",
        json={
            "organization_id": str(organization.id),
            "display_name": "Test Venue",
            "description": "A venue for testing.",
            "theme": "Sports",
            "location_name": "Test Stadium",
            "location_coords": {"lat": 48.8584, "long": 2.2945},
        },
    )
    response.raise_for_status()
    data = response.json()

    assert len(data) == 11
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["display_name"] == "Test Venue"
    assert data["description"] == "A venue for testing."
    assert data["theme"] == "Sports"
    assert data["location_name"] == "Test Stadium"
    assert data["location_coords"] == {"lat": 48.8584, "long": 2.2945}
    assert data["thumbnail"] is None
    assert data["banner"] is None
    assert data["events"] == []
    assert data["organization"]["id"] == str(organization.id)
    assert data["organization"]["display_name"] == "Test Organization"

    async with make_session() as session, session.begin():
        persisted = await session.get(Venue, uuid.UUID(data["id"]))
        assert persisted is not None
        assert persisted.id == uuid.UUID(data["id"])


@pytest.mark.asyncio
async def test_create_venue_nonexistent_organization(
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
        session.add(user)

    organization_id = uuid.uuid4()
    client = TestClient(app)
    response = client.post(
        "/api/venues",
        json={
            "organization_id": str(organization_id),
            "display_name": "Test Venue",
            "description": "A venue for testing.",
            "theme": "Sports",
            "location_name": "Test Stadium",
            "location_coords": {"lat": 48.8584, "long": 2.2945},
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": f"Organization not found: {organization_id}"}


@pytest.mark.asyncio
async def test_create_venue_non_member(
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
        session.add_all([user, organization])

    client = TestClient(app)
    response = client.post(
        "/api/venues",
        json={
            "organization_id": str(organization.id),
            "display_name": "Test Venue",
            "description": "A venue for testing.",
            "theme": "Sports",
            "location_name": "Test Stadium",
            "location_coords": {"lat": 48.8584, "long": 2.2945},
        },
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": f"User ({user.id}) is not a member of organization ({organization.id})"
    }


@pytest.mark.asyncio
async def test_create_venue_member_insufficient_permissions(
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
        session.add_all([user, organization, member])

    client = TestClient(app)
    response = client.post(
        "/api/venues",
        json={
            "organization_id": str(organization.id),
            "display_name": "Test Venue",
            "description": "A venue for testing.",
            "theme": "Sports",
            "location_name": "Test Stadium",
            "location_coords": {"lat": 48.8584, "long": 2.2945},
        },
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            f"Organization member ((UUID('{organization.id}'), UUID('{user.id}'))) "
            "missing permissions: ADMINISTRATOR"
        )
    }


@pytest.mark.asyncio
async def test_create_venue_reached_limit(
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
        for i in range(VENUE_LIMIT):
            session.add(
                Venue(
                    organization_id=organization.id,
                    display_name=f"Test Venue {i}",
                    description="A venue for testing.",
                    theme="Sports",
                    location_name="Test Stadium",
                    location_coords=None,
                )
            )

    client = TestClient(app)
    response = client.post(
        "/api/venues",
        json={
            "organization_id": str(organization.id),
            "display_name": "One Venue Too Many",
            "description": "A venue for testing.",
            "theme": "Sports",
            "location_name": "Test Stadium",
            "location_coords": {"lat": 48.8584, "long": 2.2945},
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": f"Reached maximum venue limit: {VENUE_LIMIT}"}
