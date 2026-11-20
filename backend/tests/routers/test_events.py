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
    User,
    Venue,
)
from tests.conftest import (
    AuthController,
    DatasetLoader,
    assert_validation_error,
    isoformat,
)
from tests.dataset import Dataset

EVENT_KEYS = frozenset(
    {
        "banner",
        "created_at",
        "description",
        "display_name",
        "ends_at",
        "id",
        "max_attendees",
        "starts_at",
        "category",
        "thumbnail",
        "ticket_price",
        "tickets",
        "venue",
    },
)
"""The keys served by :class:`quickticket.routers.events.EventRead`."""


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
                "category": expected.category,
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
                    "category": expected.venue.category,
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


@pytest.mark.parametrize(
    ("organization_id", "expected_ids"),
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


async def test_get_events_empty_database(client: AsyncClient) -> None:
    response = await client.get("/api/events")
    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "next": None,
        "total": 0,
    }


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

    assert set(data) == EVENT_KEYS
    assert data["id"] == str(event.id)
    assert data["created_at"] is not None
    assert data["display_name"] == event.display_name
    assert data["description"] == event.description
    assert data["category"] == event.category
    assert data["thumbnail"] is None
    assert data["banner"] is None
    assert datetime.fromisoformat(data["starts_at"]) == event.starts_at
    assert datetime.fromisoformat(data["ends_at"]) == event.ends_at
    assert data["ticket_price"] == event.ticket_price.model_dump()
    assert data["max_attendees"] == event.max_attendees
    assert data["tickets"] == []

    assert set(data["venue"]) == {
        "id",
        "created_at",
        "display_name",
        "description",
        "category",
        "thumbnail",
        "banner",
        "location_name",
        "location_coords",
        "organization",
    }
    assert data["venue"]["id"] == str(venue.id)
    assert data["venue"]["created_at"] is not None
    assert data["venue"]["display_name"] == venue.display_name
    assert data["venue"]["description"] == venue.description
    assert data["venue"]["category"] == venue.category
    assert data["venue"]["thumbnail"] is None
    assert data["venue"]["banner"] is None
    assert data["venue"]["location_name"] == venue.location_name
    assert data["venue"]["location_coords"] == venue.location_coords.model_dump()

    assert set(data["venue"]["organization"]) == {"id", "created_at", "display_name"}
    assert data["venue"]["organization"]["id"] == str(organization.id)
    assert data["venue"]["organization"]["created_at"] is not None
    assert data["venue"]["organization"]["display_name"] == organization.display_name


async def test_get_event_not_found(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()

    response = await client.get("/api/events/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


def _create_event_payload(
    *,
    venue_id: UUID | str = "00000000-0000-0000-0000-000000000000",
    display_name: str = "Test Hockey Tournament",
    description: str = "A mock hockey game, for testing.",
    category: str = "Sports",
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
    max_attendees: int = 500,
    ticket_price: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build an event creation payload, defaulting to an otherwise valid body."""
    if starts_at is None:
        starts_at = datetime.now(UTC) + timedelta(days=1)
    if ends_at is None:
        ends_at = starts_at + timedelta(hours=4)
    return {
        "venue_id": str(venue_id),
        "display_name": display_name,
        "description": description,
        "category": category,
        "starts_at": isoformat(starts_at),
        "ends_at": isoformat(ends_at),
        "max_attendees": max_attendees,
        "ticket_price": {"amount": 50, "currency": "CAD"} if ticket_price is None else ticket_price,
    }


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
            user_id=user.id,
            permissions=OrganizationMemberPermissions.OWNER,
        )
        venue = Venue(
            organization_id=organization.id,
            display_name="Test Venue",
            description="A venue for testing.",
            category="Sports",
            location_name="Test Stadium",
        )
        session.add_all([organization, member, venue])

    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=4)
    response = await client.post(
        "/api/events",
        json=_create_event_payload(venue_id=venue.id, starts_at=starts_at, ends_at=ends_at),
    )
    assert response.status_code == 201
    data = response.json()
    assert response.headers.get_list("location") == [f"https://test/api/events/{data['id']}"]

    assert set(data) == EVENT_KEYS
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

    assert data["venue"]["description"] == "A venue for testing."
    assert data["venue"]["category"] == "Sports"
    assert data["venue"]["location_name"] == "Test Stadium"
    assert data["venue"]["location_coords"] is None

    async with make_session.begin() as session:
        persisted = await session.get(Event, UUID(data["id"]))
        assert persisted is not None
        assert persisted.id == UUID(data["id"])


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
            user_id=user.id,
            permissions=OrganizationMemberPermissions(0),
        )
        venue = Venue(
            organization_id=organization.id,
            display_name="Test Venue",
            description="A venue for testing.",
            category="Sports",
            location_name="Test Stadium",
        )
        session.add_all([organization, member, venue])

    response = await client.post(
        "/api/events",
        json=_create_event_payload(venue_id=venue.id),
    )
    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            f"Organization member ({organization.id}, {user.id}) missing permissions: OWNER"
        ),
    }


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
            user_id=user.id,
            permissions=OrganizationMemberPermissions.OWNER,
        )
        session.add_all([organization, member])

    response = await client.post(
        "/api/events",
        json=_create_event_payload(),
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Venue not found: 00000000-0000-0000-0000-000000000000"}


async def test_create_event_rejects_max_attendees_below_minimum(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/events",
        json=_create_event_payload(max_attendees=-1),
    )
    assert response.status_code == 422


async def test_create_event_rejects_max_attendees_above_maximum(
    client: AsyncClient,
) -> None:
    response = await client.post(
        "/api/events",
        json=_create_event_payload(max_attendees=10001),
    )
    assert response.status_code == 422


async def test_create_event_rejects_naive_datetimes(
    client: AsyncClient,
) -> None:
    starts_at = datetime.now() + timedelta(days=1)  # noqa: DTZ005
    response = await client.post(
        "/api/events",
        json=_create_event_payload(starts_at=starts_at, ends_at=starts_at),
    )
    for field in ("starts_at", "ends_at"):
        assert_validation_error(
            response,
            loc=("body", field),
            error_type="timezone_aware",
            msg_contains="Input should have timezone info",
        )


async def test_create_event_rejects_past_datetimes(
    client: AsyncClient,
) -> None:
    starts_at = datetime.now(UTC) - timedelta(days=1)
    response = await client.post(
        "/api/events",
        json=_create_event_payload(starts_at=starts_at),
    )
    for field in ("starts_at", "ends_at"):
        assert_validation_error(
            response,
            loc=("body", field),
            error_type="datetime_future",
            msg_contains="Input should be in the future",
        )


async def test_create_event_rejects_ends_at_before_starts_at(
    client: AsyncClient,
) -> None:
    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at - timedelta(hours=1)
    response = await client.post(
        "/api/events",
        json=_create_event_payload(starts_at=starts_at, ends_at=ends_at),
    )
    assert_validation_error(
        response,
        loc=("body",),
        error_type="value_error",
        msg_contains="starts_at must be before ends_at",
    )


@pytest.mark.parametrize("offset", [timedelta(), timedelta(minutes=59)])
async def test_create_event_rejects_duration_below_minimum(
    client: AsyncClient,
    offset: timedelta,
) -> None:
    starts_at = datetime.now(UTC) + timedelta(days=1)
    response = await client.post(
        "/api/events",
        json=_create_event_payload(starts_at=starts_at, ends_at=starts_at + offset),
    )
    assert_validation_error(
        response,
        loc=("body",),
        error_type="value_error",
        msg_contains="Event duration must be between 1:00:00 and 7 days, 0:00:00",
    )


async def test_create_event_rejects_duration_above_maximum(
    client: AsyncClient,
) -> None:
    starts_at = datetime.now(UTC) + timedelta(days=1)
    response = await client.post(
        "/api/events",
        json=_create_event_payload(starts_at=starts_at, ends_at=starts_at + timedelta(days=8)),
    )
    assert_validation_error(
        response,
        loc=("body",),
        error_type="value_error",
        msg_contains="Event duration must be between 1:00:00 and 7 days, 0:00:00",
    )


async def test_edit_event(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset

    event = dataset.events[0]
    venue = next(item for item in dataset.venues if item.id == event.venue_id)
    organization = next(item for item in dataset.organizations if item.id == venue.organization_id)
    member = next(
        item for item in dataset.organization_members if item.organization_id == organization.id
    )
    auth.user = next(user for user in dataset.users if user.id == member.user_id)

    # Editing an event that has already started must still succeed.
    assert event.ends_at < datetime.now(UTC)

    response = await client.patch(
        f"/api/events/{event.id}",
        json={
            "display_name": "Edited Event",
            "description": "An edited event.",
            "category": "Comedy",
            "max_attendees": 250,
            "ticket_price": {"amount": 2500, "currency": "CAD"},
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert set(data) == EVENT_KEYS
    assert data["id"] == str(event.id)
    assert data["display_name"] == "Edited Event"
    assert data["description"] == "An edited event."
    assert data["category"] == "Comedy"
    assert data["max_attendees"] == 250
    assert data["ticket_price"] == {"amount": 2500, "currency": "CAD"}

    # Fields absent from the payload keep their seeded values.
    assert datetime.fromisoformat(data["starts_at"]) == event.starts_at
    assert datetime.fromisoformat(data["ends_at"]) == event.ends_at
    assert data["tickets"] == []
    assert data["venue"]["id"] == str(venue.id)

    fetched = await client.get(f"/api/events/{event.id}")
    assert fetched.status_code == 200
    assert fetched.json() == data


async def test_edit_event_not_found(client: AsyncClient) -> None:
    response = await client.patch(
        "/api/events/00000000-0000-0000-0000-000000000000",
        json={"display_name": "Edited Event"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


def _owner_of_event(dataset: Dataset, event: Event) -> User:
    """Return the owner of the organization that holds the event's venue."""
    venue = next(item for item in dataset.venues if item.id == event.venue_id)
    member = next(
        item
        for item in dataset.organization_members
        if item.organization_id == venue.organization_id
    )
    return next(user for user in dataset.users if user.id == member.user_id)


async def test_edit_event_dates(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    auth.user = _owner_of_event(dataset, event)

    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=4)
    response = await client.patch(
        f"/api/events/{event.id}",
        json={"starts_at": isoformat(starts_at), "ends_at": isoformat(ends_at)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["starts_at"] == isoformat(starts_at)
    assert data["ends_at"] == isoformat(ends_at)

    fetched = await client.get(f"/api/events/{event.id}")
    assert fetched.status_code == 200
    assert fetched.json() == data


async def test_edit_event_unauthenticated(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    auth.user = None

    response = await client.patch(f"/api/events/{event.id}", json={"display_name": "Edited Event"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


async def test_edit_event_non_member(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    venue = next(item for item in dataset.venues if item.id == event.venue_id)
    member_ids = {member.user_id for member in dataset.organization_members}
    auth.user = next(user for user in dataset.users if user.id not in member_ids)

    response = await client.patch(f"/api/events/{event.id}", json={"display_name": "Edited Event"})

    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            f"User ({auth.user.id}) is not a member of organization ({venue.organization_id})"
        ),
    }


async def test_edit_event_member_without_owner(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    venue = next(item for item in dataset.venues if item.id == event.venue_id)
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

    response = await client.patch(f"/api/events/{event.id}", json={"display_name": "Edited Event"})

    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            f"Organization member ({venue.organization_id}, {auth.user.id}) "
            "missing permissions: OWNER"
        ),
    }


async def test_edit_event_cross_organization(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    venue = next(item for item in dataset.venues if item.id == event.venue_id)
    other_member = next(
        member
        for member in dataset.organization_members
        if member.organization_id != venue.organization_id
    )
    auth.user = next(user for user in dataset.users if user.id == other_member.user_id)

    response = await client.patch(f"/api/events/{event.id}", json={"display_name": "Edited Event"})

    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            f"User ({auth.user.id}) is not a member of organization ({venue.organization_id})"
        ),
    }


async def test_edit_event_no_fields(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    auth.user = _owner_of_event(dataset, event)

    response = await client.patch(f"/api/events/{event.id}", json={})

    assert response.status_code == 400
    assert response.json() == {"detail": "No fields to update"}


@pytest.mark.parametrize("field", ["starts_at", "ends_at"])
async def test_edit_event_requires_both_dates(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    field: str,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    auth.user = _owner_of_event(dataset, event)

    response = await client.patch(
        f"/api/events/{event.id}",
        json={field: isoformat(datetime.now(UTC) + timedelta(days=1))},
    )

    assert_validation_error(
        response,
        loc=("body",),
        error_type="value_error",
        msg_contains="Must set starts_at and ends_at together",
    )


@pytest.mark.parametrize(
    ("starts_delta", "ends_delta", "msg_contains"),
    [
        (timedelta(days=2), timedelta(days=1), "starts_at must be before ends_at"),
        (timedelta(days=1), timedelta(days=1), "Event duration must be between"),
        (timedelta(days=1), timedelta(days=1, minutes=59), "Event duration must be between"),
        (timedelta(days=1), timedelta(days=8, seconds=1), "Event duration must be between"),
    ],
)
async def test_edit_event_rejects_invalid_duration(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    starts_delta: timedelta,
    ends_delta: timedelta,
    msg_contains: str,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    auth.user = _owner_of_event(dataset, event)

    now = datetime.now(UTC)
    response = await client.patch(
        f"/api/events/{event.id}",
        json={
            "starts_at": isoformat(now + starts_delta),
            "ends_at": isoformat(now + ends_delta),
        },
    )

    assert_validation_error(
        response,
        loc=("body",),
        error_type="value_error",
        msg_contains=msg_contains,
    )


async def test_edit_event_rejects_past_datetimes(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    auth.user = _owner_of_event(dataset, event)

    starts_at = datetime.now(UTC) - timedelta(days=1)
    ends_at = starts_at + timedelta(hours=4)
    response = await client.patch(
        f"/api/events/{event.id}",
        json={"starts_at": isoformat(starts_at), "ends_at": isoformat(ends_at)},
    )

    for field in ("starts_at", "ends_at"):
        assert_validation_error(
            response,
            loc=("body", field),
            error_type="datetime_future",
            msg_contains="Input should be in the future",
        )


@pytest.mark.parametrize("duration", [timedelta(hours=1), timedelta(days=7)])
async def test_edit_event_accepts_duration_boundaries(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    duration: timedelta,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    auth.user = _owner_of_event(dataset, event)

    starts_at = datetime.now(UTC) + timedelta(days=1)
    ends_at = starts_at + duration
    response = await client.patch(
        f"/api/events/{event.id}",
        json={"starts_at": isoformat(starts_at), "ends_at": isoformat(ends_at)},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["starts_at"] == isoformat(starts_at)
    assert data["ends_at"] == isoformat(ends_at)


@pytest.mark.parametrize("max_attendees", [0, 10000])
async def test_edit_event_accepts_max_attendees_boundaries(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    max_attendees: int,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    auth.user = _owner_of_event(dataset, event)

    response = await client.patch(
        f"/api/events/{event.id}",
        json={"max_attendees": max_attendees},
    )

    assert response.status_code == 200
    assert response.json()["max_attendees"] == max_attendees


@pytest.mark.parametrize("max_attendees", [-1, 10001])
async def test_edit_event_rejects_max_attendees_out_of_range(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    max_attendees: int,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    auth.user = _owner_of_event(dataset, event)

    response = await client.patch(
        f"/api/events/{event.id}",
        json={"max_attendees": max_attendees},
    )

    assert response.status_code == 422
    locations = {tuple(error["loc"]) for error in response.json()["detail"]}
    assert ("body", "max_attendees") in locations


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("display_name", ""),
        ("display_name", "  ab "),
        ("display_name", "x" * 129),
        ("category", "x" * 129),
        ("description", "x" * 4097),
    ],
)
async def test_edit_event_rejects_invalid_fields(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    field: str,
    value: str,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    auth.user = _owner_of_event(dataset, event)

    response = await client.patch(f"/api/events/{event.id}", json={field: value})

    assert response.status_code == 422
    locations = {tuple(error["loc"]) for error in response.json()["detail"]}
    assert ("body", field) in locations


@pytest.mark.parametrize(
    "field",
    ["display_name", "description", "category", "max_attendees", "ticket_price"],
)
async def test_edit_event_rejects_null_fields(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    field: str,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    event = dataset.events[0]
    auth.user = _owner_of_event(dataset, event)

    response = await client.patch(f"/api/events/{event.id}", json={field: None})

    assert response.status_code == 422
    locations = {tuple(error["loc"]) for error in response.json()["detail"]}
    assert ("body", field) in locations
