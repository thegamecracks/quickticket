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
    User,
    Venue,
    VenueID,
)
from quickticket.routers.venues import VENUE_LIMIT
from tests.conftest import (
    AuthController,
    DatasetLoader,
    assert_validation_error,
    isoformat,
)
from tests.dataset import Dataset


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
            "category": venue.category,
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
        "category": venue.category,
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
            "category": expected.category,
            "starts_at": isoformat(expected.starts_at),
            "ends_at": isoformat(expected.ends_at),
            "ticket_price": expected.ticket_price.model_dump(),
            "max_attendees": expected.max_attendees,
            "tickets": [],
        }


async def test_get_venue_not_found(client: AsyncClient, auth: AuthController) -> None:
    auth.user = None

    response = await client.get("/api/venues/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


def _create_venue_payload(
    *,
    organization_id: UUID | str = "00000000-0000-0000-0000-000000000000",
    display_name: str = "Test Venue",
    description: str = "A venue for testing.",
    category: str = "Sports",
    location_name: str = "Test Stadium",
    location_coords: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build a venue creation payload, defaulting to an otherwise valid body."""
    return {
        "organization_id": str(organization_id),
        "display_name": display_name,
        "description": description,
        "category": category,
        "location_name": location_name,
        "location_coords": location_coords,
    }


def _owned_organization(dataset: Dataset) -> tuple[Organization, User]:
    """Return a seeded organization and one of its owners."""
    member = dataset.organization_members[0]
    organization = next(item for item in dataset.organizations if item.id == member.organization_id)
    user = next(item for item in dataset.users if item.id == member.user_id)
    return organization, user


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
            user_id=user.id,
            permissions=OrganizationMemberPermissions.OWNER,
        )
        session.add_all([organization, member])

    response = await client.post(
        "/api/venues",
        json=_create_venue_payload(
            organization_id=organization.id,
            location_coords={"lat": 48.8584, "lng": 2.2945},
        ),
    )
    assert response.status_code == 201
    data = response.json()
    assert response.headers.get_list("location") == [f"https://test/api/venues/{data['id']}"]

    assert set(data) == VENUE_KEYS
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["display_name"] == "Test Venue"
    assert data["description"] == "A venue for testing."
    assert data["category"] == "Sports"
    assert data["location_name"] == "Test Stadium"
    assert data["location_coords"] == {"lat": 48.8584, "lng": 2.2945}
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
        assert persisted.category == "Sports"
        assert persisted.location_name == "Test Stadium"
        assert persisted.location_coords == Point(lat=48.8584, lng=2.2945)


async def test_create_venue_preserves_multiline_description(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    organization, owner = _owned_organization(dataset_loader.dataset)
    auth.user = owner

    response = await client.post(
        "/api/venues",
        json=_create_venue_payload(
            organization_id=organization.id,
            description="  ## About\n\nDoors at 7.\n\tBring ID.  ",
        ),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "## About\n\nDoors at 7.\n\tBring ID."

    fetched = await client.get(f"/api/venues/{data['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == data


@pytest.mark.parametrize("field", ["category", "location_name"])
async def test_create_venue_collapses_oneline_fields(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    field: str,
) -> None:
    await dataset_loader.load()
    organization, owner = _owned_organization(dataset_loader.dataset)
    auth.user = owner

    payload = _create_venue_payload(organization_id=organization.id)
    payload[field] = "  Sports \u00a0\t\n Hall  "
    response = await client.post("/api/venues", json=payload)

    assert response.status_code == 201
    assert response.json()[field] == "Sports Hall"


async def test_create_venue_accepts_whitespace_only_description(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    organization, owner = _owned_organization(dataset_loader.dataset)
    auth.user = owner

    response = await client.post(
        "/api/venues",
        json=_create_venue_payload(
            organization_id=organization.id,
            description="\n\n  \t\n",
        ),
    )

    assert response.status_code == 201
    assert response.json()["description"] == ""


@pytest.mark.parametrize(
    "field",
    ["organization_id", "display_name", "description", "category", "location_name"],
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
            user_id=user.id,
            permissions=OrganizationMemberPermissions.OWNER,
        )
        session.add_all([organization, member])

    payload = _create_venue_payload(
        organization_id=organization.id,
        location_coords={"lat": 48.8584, "lng": 2.2945},
    )
    payload.pop(field)

    response = await client.post("/api/venues", json=payload)

    assert response.status_code == 422
    locations = {tuple(item["loc"]) for item in response.json()["detail"]}
    assert ("body", field) in locations


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
            user_id=user.id,
            permissions=OrganizationMemberPermissions.OWNER,
        )
        session.add_all([organization, member])

    response = await client.post(
        "/api/venues",
        json=_create_venue_payload(
            organization_id=organization.id,
            display_name="Virtual Venue",
            description="A venue for testing online events.",
            category="Music",
            location_name="Zoom",
            location_coords=None,
        ),
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
            user_id=user.id,
            permissions=OrganizationMemberPermissions.OWNER,
        )
        session.add_all([organization, member])

    auth.user = None
    response = await client.post(
        "/api/venues",
        json=_create_venue_payload(
            organization_id=organization.id,
            location_coords={"lat": 48.8584, "lng": 2.2945},
        ),
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


async def test_create_venue_nonexistent_organization(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    response = await client.post(
        "/api/venues",
        json=_create_venue_payload(location_coords={"lat": 48.8584, "lng": 2.2945}),
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Organization not found: 00000000-0000-0000-0000-000000000000",
    }


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
        json=_create_venue_payload(
            organization_id=organization.id,
            location_coords={"lat": 48.8584, "lng": 2.2945},
        ),
    )
    assert response.status_code == 403
    assert response.json() == {
        "detail": f"User ({user.id}) is not a member of organization ({organization.id})",
    }


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
            user_id=user.id,
            permissions=OrganizationMemberPermissions(0),
        )
        session.add_all([organization, member])

    response = await client.post(
        "/api/venues",
        json=_create_venue_payload(
            organization_id=organization.id,
            location_coords={"lat": 48.8584, "lng": 2.2945},
        ),
    )
    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            f"Organization member ({organization.id}, {user.id}) missing permissions: OWNER"
        ),
    }


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
            user_id=user.id,
            permissions=OrganizationMemberPermissions.OWNER,
        )
        session.add_all([organization, member])

    for i in range(VENUE_LIMIT):
        allowed = await client.post(
            "/api/venues",
            json=_create_venue_payload(
                organization_id=organization.id,
                display_name=f"Test Venue {i}",
                location_coords={"lat": 48.8584, "lng": 2.2945},
            ),
        )
        assert allowed.status_code == 201

    response = await client.post(
        "/api/venues",
        json=_create_venue_payload(
            organization_id=organization.id,
            display_name="One Venue Too Many",
            location_coords={"lat": 48.8584, "lng": 2.2945},
        ),
    )
    assert response.status_code == 400
    assert response.json() == {"detail": f"Reached maximum venue limit: {VENUE_LIMIT}"}


async def test_create_venue_rejects_unknown_field(client: AsyncClient) -> None:
    payload = _create_venue_payload(location_coords={"lat": 48.8584, "lng": 2.2945})
    payload["bogus"] = "x"

    response = await client.post("/api/venues", json=payload)

    assert_validation_error(
        response,
        loc=("body", "bogus"),
        error_type="extra_forbidden",
        msg_contains="Extra inputs are not permitted",
    )


async def test_create_venue_rejects_unknown_location_coords_field(client: AsyncClient) -> None:
    payload = _create_venue_payload(
        location_coords={"lat": 48.8584, "lng": 2.2945, "bogus": 1},
    )

    response = await client.post("/api/venues", json=payload)

    assert_validation_error(
        response,
        loc=("body", "location_coords", "bogus"),
        error_type="extra_forbidden",
        msg_contains="Extra inputs are not permitted",
    )


VENUE_KEYS = frozenset(
    {
        "category",
        "created_at",
        "description",
        "display_name",
        "events",
        "id",
        "location_coords",
        "location_name",
        "organization",
    },
)
"""The keys served by :class:`quickticket.routers.venues.VenueRead`."""


def _owner_of_venue(dataset: Dataset, venue: Venue) -> User:
    """Return the owner of the organization that holds the venue."""
    member = next(
        item
        for item in dataset.organization_members
        if item.organization_id == venue.organization_id
    )
    return next(user for user in dataset.users if user.id == member.user_id)


async def test_edit_venue(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    venue = dataset.venues[0]
    organization = next(item for item in dataset.organizations if item.id == venue.organization_id)
    expected_events = [item for item in dataset.events if item.venue_id == venue.id]
    auth.user = _owner_of_venue(dataset, venue)

    response = await client.patch(
        f"/api/venues/{venue.id}",
        json={
            "display_name": "Edited Venue",
            "description": "An edited venue.",
            "category": "Comedy",
            "location_name": "Edited Hall",
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert set(data) == VENUE_KEYS
    assert data["id"] == str(venue.id)
    assert data["display_name"] == "Edited Venue"
    assert data["description"] == "An edited venue."
    assert data["category"] == "Comedy"
    assert data["location_name"] == "Edited Hall"

    # Fields absent from the payload keep their seeded values.
    assert venue.location_coords is not None
    assert data["location_coords"] == venue.location_coords.model_dump()
    assert {event["id"] for event in data["events"]} == {str(event.id) for event in expected_events}
    assert all(event["tickets"] == [] for event in data["events"])
    assert data["organization"]["id"] == str(organization.id)

    fetched = await client.get(f"/api/venues/{venue.id}")
    assert fetched.status_code == 200
    assert fetched.json() == data


async def test_edit_venue_preserves_multiline_description(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    venue = dataset.venues[0]
    auth.user = _owner_of_venue(dataset, venue)

    response = await client.patch(
        f"/api/venues/{venue.id}",
        json={"description": "Line one\n\nLine two"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Line one\n\nLine two"

    fetched = await client.get(f"/api/venues/{venue.id}")
    assert fetched.status_code == 200
    assert fetched.json() == data


async def test_edit_venue_location_coords(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    venue = dataset.venues[0]
    auth.user = _owner_of_venue(dataset, venue)

    response = await client.patch(
        f"/api/venues/{venue.id}",
        json={"location_coords": {"lat": 48.8584, "lng": 2.2945}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["location_coords"] == {"lat": 48.8584, "lng": 2.2945}

    fetched = await client.get(f"/api/venues/{venue.id}")
    assert fetched.status_code == 200
    assert fetched.json() == data


async def test_edit_venue_clears_location_coords(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    venue = dataset.venues[0]
    assert venue.location_coords is not None
    auth.user = _owner_of_venue(dataset, venue)

    response = await client.patch(
        f"/api/venues/{venue.id}",
        json={"location_coords": None},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["location_coords"] is None

    fetched = await client.get(f"/api/venues/{venue.id}")
    assert fetched.status_code == 200
    assert fetched.json()["location_coords"] is None


async def test_edit_venue_not_found(client: AsyncClient) -> None:
    response = await client.patch(
        "/api/venues/00000000-0000-0000-0000-000000000000",
        json={"display_name": "Edited Venue"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


async def test_edit_venue_unauthenticated(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    venue = dataset.venues[0]
    auth.user = None

    response = await client.patch(
        f"/api/venues/{venue.id}",
        json={"display_name": "Edited Venue"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


async def test_edit_venue_non_member(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    venue = dataset.venues[0]
    member_ids = {member.user_id for member in dataset.organization_members}
    auth.user = next(user for user in dataset.users if user.id not in member_ids)

    response = await client.patch(
        f"/api/venues/{venue.id}",
        json={"display_name": "Edited Venue"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            f"User ({auth.user.id}) is not a member of organization ({venue.organization_id})"
        ),
    }


async def test_edit_venue_member_without_owner(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    dataset = dataset_loader.dataset
    venue = dataset.venues[0]
    member = next(
        item
        for item in dataset.organization_members
        if item.organization_id == venue.organization_id
    )
    # Downgrade the member before loading so the request authenticates as a
    # member that lacks the OWNER permission.
    member.permissions = OrganizationMemberPermissions(0)
    await dataset_loader.load()
    auth.user = next(user for user in dataset.users if user.id == member.user_id)

    response = await client.patch(
        f"/api/venues/{venue.id}",
        json={"display_name": "Edited Venue"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            f"Organization member ({venue.organization_id}, {auth.user.id}) "
            "missing permissions: OWNER"
        ),
    }


async def test_edit_venue_cross_organization(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    venue = dataset.venues[0]
    other_member = next(
        member
        for member in dataset.organization_members
        if member.organization_id != venue.organization_id
    )
    auth.user = next(user for user in dataset.users if user.id == other_member.user_id)

    response = await client.patch(
        f"/api/venues/{venue.id}",
        json={"display_name": "Edited Venue"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            f"User ({auth.user.id}) is not a member of organization ({venue.organization_id})"
        ),
    }


async def test_edit_venue_no_fields(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    venue = dataset.venues[0]
    auth.user = _owner_of_venue(dataset, venue)

    response = await client.patch(f"/api/venues/{venue.id}", json={})

    assert response.status_code == 400
    assert response.json() == {"detail": "No fields to update"}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("display_name", ""),
        ("display_name", "  ab "),
        ("display_name", "x" * 129),
        ("category", "x" * 129),
        ("description", "x" * 4097),
        ("location_name", "x" * 129),
    ],
)
async def test_edit_venue_rejects_invalid_fields(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    field: str,
    value: str,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    venue = dataset.venues[0]
    auth.user = _owner_of_venue(dataset, venue)

    response = await client.patch(f"/api/venues/{venue.id}", json={field: value})

    assert response.status_code == 422
    locations = {tuple(error["loc"]) for error in response.json()["detail"]}
    assert ("body", field) in locations


@pytest.mark.parametrize("field", ["display_name", "description", "category", "location_name"])
async def test_edit_venue_rejects_null_fields(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    field: str,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    venue = dataset.venues[0]
    auth.user = _owner_of_venue(dataset, venue)

    response = await client.patch(f"/api/venues/{venue.id}", json={field: None})

    assert response.status_code == 422
    locations = {tuple(error["loc"]) for error in response.json()["detail"]}
    assert ("body", field) in locations


@pytest.mark.parametrize(
    "changes",
    [
        {"bogus": "x"},
        {"display_name": "Changed", "bogus": "x"},
    ],
)
async def test_edit_venue_rejects_unknown_field(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    changes: dict[str, object],
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    venue = dataset.venues[0]
    auth.user = _owner_of_venue(dataset, venue)

    response = await client.patch(f"/api/venues/{venue.id}", json=changes)

    assert_validation_error(
        response,
        loc=("body", "bogus"),
        error_type="extra_forbidden",
        msg_contains="Extra inputs are not permitted",
    )

    fetched = await client.get(f"/api/venues/{venue.id}")
    assert fetched.status_code == 200
    assert fetched.json()["display_name"] == venue.display_name


@pytest.mark.parametrize(
    "changes",
    [
        {"location_coords": {"lat": 48.8584, "lng": 2.2945, "bogus": 1}},
        {
            "display_name": "Changed",
            "location_coords": {"lat": 48.8584, "lng": 2.2945, "bogus": 1},
        },
    ],
)
async def test_edit_venue_rejects_unknown_location_coords_field(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    changes: dict[str, object],
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    venue = dataset.venues[0]
    assert venue.location_coords is not None
    auth.user = _owner_of_venue(dataset, venue)

    response = await client.patch(f"/api/venues/{venue.id}", json=changes)

    assert_validation_error(
        response,
        loc=("body", "location_coords", "bogus"),
        error_type="extra_forbidden",
        msg_contains="Extra inputs are not permitted",
    )

    fetched = await client.get(f"/api/venues/{venue.id}")
    assert fetched.status_code == 200
    data = fetched.json()
    assert data["display_name"] == venue.display_name
    assert data["location_coords"] == venue.location_coords.model_dump()
