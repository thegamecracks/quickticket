from collections import defaultdict
from uuid import UUID

import pytest
from httpx2 import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import (
    Event,
    EventID,
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    Point,
    Venue,
    VenueID,
)
from quickticket.routers.venues import VENUE_LIMIT
from tests.conftest import AuthController, DatasetLoader, isoformat


@pytest.mark.asyncio
async def test_get_venues(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset

    response = await client.get("/api/venues")
    assert response.status_code == 200
    data = response.json()

    assert set(data) == {"items", "next", "total"}
    assert data["total"] == len(dataset.venues)
    assert data["next"] is None
    assert len(data["items"]) == len(dataset.venues)

    venues = {venue.id: venue for venue in dataset.venues}
    organizations = {organization.id: organization for organization in dataset.organizations}
    events: defaultdict[UUID, list[Event]] = defaultdict(list)
    for event in dataset.events:
        events[event.venue_id].append(event)

    assert {VenueID(UUID(item["id"])) for item in data["items"]} == set(venues)
    for item in data["items"]:
        venue = venues[VenueID(UUID(item["id"]))]
        organization = organizations[venue.organization_id]

        item_events = item.pop("events")
        assert {EventID(UUID(event["id"])) for event in item_events} == {
            event.id for event in events[venue.id]
        }
        assert all(event["tickets"] == [] for event in item_events)

        assert item == {
            "id": str(venue.id),
            "created_at": isoformat(venue.created_at),
            "display_name": venue.display_name,
            "description": venue.description,
            "theme": venue.theme,
            "thumbnail": None,
            "banner": None,
            "location_name": venue.location_name,
            "location_coords": venue.location_coords.model_dump()
            if venue.location_coords is not None
            else None,
            "organization": {
                "id": str(organization.id),
                "created_at": isoformat(organization.created_at),
                "display_name": organization.display_name,
            },
        }


@pytest.mark.asyncio
async def test_get_venues_before_filters_total(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    ordered = sorted(dataset.venues, key=lambda venue: venue.created_at, reverse=True)

    # before is a filter: it excludes the four newest venues.
    response = await client.get("/api/venues", params={"before": isoformat(ordered[3].created_at)})
    assert response.status_code == 200
    data = response.json()

    assert [venue["id"] for venue in data["items"]] == [str(venue.id) for venue in ordered[4:]]
    assert data["next"] is None
    assert data["total"] == len(ordered) - 4


@pytest.mark.asyncio
async def test_get_venue(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    auth.user = None

    event = dataset.events[0]
    venue = next(item for item in dataset.venues if item.id == event.venue_id)
    organization = next(item for item in dataset.organizations if item.id == venue.organization_id)
    expected_events = [item for item in dataset.events if item.venue_id == venue.id]

    response = await client.get(f"/api/venues/{venue.id}")
    assert response.status_code == 200
    data = response.json()

    events = data.pop("events")
    assert data == {
        "id": str(venue.id),
        "created_at": isoformat(venue.created_at),
        "display_name": venue.display_name,
        "description": venue.description,
        "theme": venue.theme,
        "thumbnail": None,
        "banner": None,
        "location_name": venue.location_name,
        "location_coords": venue.location_coords.model_dump()
        if venue.location_coords is not None
        else None,
        "organization": {
            "id": str(organization.id),
            "created_at": isoformat(organization.created_at),
            "display_name": organization.display_name,
        },
    }

    assert {item["id"] for item in events} == {str(item.id) for item in expected_events}
    for item in events:
        expected = next(event for event in expected_events if str(event.id) == item["id"])
        assert item == {
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
        }


@pytest.mark.asyncio
async def test_get_venue_not_found(client: AsyncClient, auth: AuthController) -> None:
    auth.user = None

    response = await client.get("/api/venues/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


@pytest.mark.asyncio
async def test_create_venue(
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

    response = await client.post(
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
    assert response.status_code == 201
    data = response.json()
    assert response.headers.get_list("location") == [f"http://test/api/venues/{data['id']}"]

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

    async with make_session.begin() as session:
        persisted = await session.get(Venue, UUID(data["id"]))
        assert persisted is not None
        assert persisted.id == UUID(data["id"])
        assert persisted.organization_id == organization.id
        assert persisted.display_name == "Test Venue"
        assert persisted.description == "A venue for testing."
        assert persisted.theme == "Sports"
        assert persisted.location_name == "Test Stadium"
        assert persisted.location_coords == Point(lat=48.8584, long=2.2945)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field",
    ["organization_id", "display_name", "description", "theme", "location_name"],
)
async def test_create_venue_missing_required_field(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
    field: str,
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

    payload = {
        "organization_id": str(organization.id),
        "display_name": "Test Venue",
        "description": "A venue for testing.",
        "theme": "Sports",
        "location_name": "Test Stadium",
        "location_coords": {"lat": 48.8584, "long": 2.2945},
    }
    payload.pop(field)

    response = await client.post("/api/venues", json=payload)

    assert response.status_code == 422
    locations = {tuple(item["loc"]) for item in response.json()["detail"]}
    assert ("body", field) in locations


@pytest.mark.asyncio
async def test_create_venue_without_location_coords(
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

    response = await client.post(
        "/api/venues",
        json={
            "organization_id": str(organization.id),
            "display_name": "Virtual Venue",
            "description": "A venue for testing online events.",
            "theme": "Music",
            "location_name": "Zoom",
            "location_coords": None,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["location_name"] == "Zoom"
    assert data["location_coords"] is None
    assert data["events"] == []

    async with make_session.begin() as session:
        persisted = await session.get(Venue, UUID(data["id"]))
        assert persisted is not None
        assert persisted.location_name == "Zoom"
        assert persisted.location_coords is None

    auth.user = None
    fetched = await client.get(f"/api/venues/{data['id']}")
    assert fetched.status_code == 200
    fetched_data = fetched.json()
    assert fetched_data["display_name"] == "Virtual Venue"
    assert fetched_data["location_name"] == "Zoom"
    assert fetched_data["location_coords"] is None
    assert fetched_data["events"] == []
    assert fetched_data["organization"]["id"] == str(organization.id)


@pytest.mark.asyncio
async def test_create_venue_unauthenticated(
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

    auth.user = None
    response = await client.post(
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

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_create_venue_nonexistent_organization(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    response = await client.post(
        "/api/venues",
        json={
            "organization_id": "00000000-0000-0000-0000-000000000000",
            "display_name": "Test Venue",
            "description": "A venue for testing.",
            "theme": "Sports",
            "location_name": "Test Stadium",
            "location_coords": {"lat": 48.8584, "long": 2.2945},
        },
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Organization not found: 00000000-0000-0000-0000-000000000000",
    }


@pytest.mark.asyncio
async def test_create_venue_non_member(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    user = auth.user
    async with make_session.begin() as session:
        organization = Organization(display_name="Test Organization")
        session.add(organization)

    response = await client.post(
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
    assert response.status_code == 403
    assert response.json() == {
        "detail": f"User ({user.id}) is not a member of organization ({organization.id})",
    }


@pytest.mark.asyncio
async def test_create_venue_member_insufficient_permissions(
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
        session.add_all([organization, member])

    response = await client.post(
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
    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            f"Organization member ({organization.id}, {user.id}) missing permissions: ADMINISTRATOR"
        ),
    }


@pytest.mark.asyncio
async def test_create_venue_reached_limit(
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

    for i in range(VENUE_LIMIT):
        allowed = await client.post(
            "/api/venues",
            json={
                "organization_id": str(organization.id),
                "display_name": f"Test Venue {i}",
                "description": "A venue for testing.",
                "theme": "Sports",
                "location_name": "Test Stadium",
                "location_coords": {"lat": 48.8584, "long": 2.2945},
            },
        )
        assert allowed.status_code == 201

    response = await client.post(
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
