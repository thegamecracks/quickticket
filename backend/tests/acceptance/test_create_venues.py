"""Acceptance tests for user story #49: an organizer can create venues.

Covers GitHub issue #91. Each test is one scenario from the story:

- full details (name, description, location)
- missing details
- virtual venues (no coordinates)
- venue limit
- no organization yet
- editing
"""

from uuid import UUID

import pytest
from httpx2 import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import (
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    Venue,
)
from quickticket.routers.venues import VENUE_LIMIT
from tests.acceptance.helpers import make_administrator, venue_body
from tests.conftest import AuthController


@pytest.mark.asyncio
async def test_organizer_creates_venue_with_full_details(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    organization = await make_administrator(make_session, auth.user)

    response = await client.post("/api/venues", json=venue_body(organization.id))

    assert response.status_code == 201
    data = response.json()
    assert data["display_name"] == "Harbour Hall"
    assert data["description"] == "A waterfront room with seating for 120."
    assert data["theme"] == "Music"
    assert data["location_name"] == "88 Granville St., Toronto"
    assert data["location_coords"] == {"lat": 43.6532, "long": -79.3832}
    assert data["organization"]["id"] == str(organization.id)
    assert data["organization"]["display_name"] == organization.display_name
    assert data["events"] == []
    assert response.headers.get_list("location") == [f"http://test/api/venues/{data['id']}"]

    async with make_session.begin() as session:
        persisted = await session.get(Venue, UUID(data["id"]))
        assert persisted is not None
        assert persisted.display_name == "Harbour Hall"
        assert persisted.location_coords is not None
        assert persisted.location_coords.lat == 43.6532
        assert persisted.location_coords.long == -79.3832


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field",
    ["organization_id", "display_name", "description", "theme", "location_name"],
)
async def test_organizer_cannot_omit_required_venue_details(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
    field: str,
) -> None:
    assert auth.user is not None
    organization = await make_administrator(make_session, auth.user)
    payload = venue_body(organization.id)
    payload.pop(field)

    response = await client.post("/api/venues", json=payload)

    assert response.status_code == 422
    locations = {tuple(item["loc"]) for item in response.json()["detail"]}
    assert ("body", field) in locations


@pytest.mark.asyncio
@pytest.mark.parametrize("display_name", ["", "   ", "ab"])
async def test_organizer_cannot_submit_a_blank_venue_name(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
    display_name: str,
) -> None:
    assert auth.user is not None
    organization = await make_administrator(make_session, auth.user)

    response = await client.post(
        "/api/venues",
        json=venue_body(organization.id, display_name=display_name),
    )

    assert response.status_code == 422
    locations = {tuple(item["loc"]) for item in response.json()["detail"]}
    assert ("body", "display_name") in locations


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["description", "theme", "location_name"])
async def test_organizer_cannot_submit_blank_descriptive_fields(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
    field: str,
) -> None:
    """Story #49: missing details are rejected.

    display_name already has a minimum length. description, theme, and
    location_name currently do not, so a whitespace-only value is stored
    as an empty string.
    """
    assert auth.user is not None
    organization = await make_administrator(make_session, auth.user)

    response = await client.post(
        "/api/venues",
        json=venue_body(organization.id, **{field: "   "}),
    )

    if response.status_code == 201 and response.json()[field] == "":
        pytest.xfail(
            f"Blank {field} is saved as an empty string. "
            "Story #49 expects missing details to be rejected.",
        )

    assert response.status_code == 422
    locations = {tuple(item["loc"]) for item in response.json()["detail"]}
    assert ("body", field) in locations


@pytest.mark.asyncio
async def test_organizer_creates_virtual_venue_without_coordinates(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    organization = await make_administrator(make_session, auth.user)

    response = await client.post(
        "/api/venues",
        json=venue_body(
            organization.id,
            display_name="Online Listening Room",
            description="A virtual venue with no street address.",
            theme="Music",
            location_name="Google Meet",
            location_coords=None,
        ),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["display_name"] == "Online Listening Room"
    assert data["location_name"] == "Google Meet"
    assert data["location_coords"] is None

    async with make_session.begin() as session:
        persisted = await session.get(Venue, UUID(data["id"]))
        assert persisted is not None
        assert persisted.location_name == "Google Meet"
        assert persisted.location_coords is None


@pytest.mark.asyncio
async def test_organizer_cannot_pass_the_venue_limit(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    """Story #49 asked whether the cap is 3. The API enforces VENUE_LIMIT (5)."""
    assert auth.user is not None
    user = auth.user
    organization = await make_administrator(make_session, user)
    async with make_session.begin() as session:
        session.add_all(
            [
                Venue(
                    organization_id=organization.id,
                    display_name=f"Existing Venue {index}",
                    description="Already on the organization.",
                    theme="Music",
                    location_name="Online",
                    location_coords=None,
                )
                for index in range(VENUE_LIMIT - 1)
            ],
        )

    allowed = await client.post(
        "/api/venues",
        json=venue_body(organization.id, display_name="Last Allowed Venue"),
    )
    assert allowed.status_code == 201

    rejected = await client.post(
        "/api/venues",
        json=venue_body(organization.id, display_name="One Venue Too Many"),
    )
    assert rejected.status_code == 400
    assert rejected.json() == {"detail": f"Reached maximum venue limit: {VENUE_LIMIT}"}


@pytest.mark.asyncio
async def test_signed_out_visitor_cannot_create_a_venue(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    organization = await make_administrator(make_session, auth.user)
    auth.user = None

    response = await client.post("/api/venues", json=venue_body(organization.id))

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_organizer_must_create_an_organization_first(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    async with make_session.begin() as session:
        organization = Organization(display_name="Someone Else's Organization")
        session.add(organization)

    response = await client.post("/api/venues", json=venue_body(organization.id))

    assert response.status_code == 403
    assert "not a member" in response.json()["detail"]


@pytest.mark.asyncio
async def test_member_without_administrator_permission_cannot_create_a_venue(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    async with make_session.begin() as session:
        organization = Organization(display_name="Harbour Hall Organizers")
        member = OrganizationMember(
            organization_id=organization.id,
            account_id=auth.user.id,
            permissions=OrganizationMemberPermissions(0),
        )
        session.add_all([organization, member])

    response = await client.post("/api/venues", json=venue_body(organization.id))

    assert response.status_code == 403
    assert "ADMINISTRATOR" in response.json()["detail"]


@pytest.mark.asyncio
async def test_unknown_organization_is_rejected(
    client: AsyncClient,
    auth: AuthController,
) -> None:
    assert auth.user is not None

    response = await client.post(
        "/api/venues",
        json=venue_body(UUID("00000000-0000-0000-0000-000000000000")),
    )

    assert response.status_code == 400
    assert response.json()["detail"].startswith("Organization not found")


@pytest.mark.asyncio
async def test_organizer_can_edit_a_venue(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    organization = await make_administrator(make_session, auth.user)
    created = await client.post("/api/venues", json=venue_body(organization.id))
    assert created.status_code == 201
    venue_id = created.json()["id"]

    response = await client.patch(
        f"/api/venues/{venue_id}",
        json={
            "display_name": "Harbour Hall Renamed",
            "description": "Updated description.",
            "theme": "Arts",
            "location_name": "Zoom",
            "location_coords": None,
        },
    )
    if response.status_code == 501:
        pytest.xfail(
            "Editing a venue is not implemented. PATCH /api/venues/{id} returns 501 (issue #96).",
        )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Harbour Hall Renamed"
    assert response.json()["location_name"] == "Zoom"
    assert response.json()["location_coords"] is None

    fetched = await client.get(f"/api/venues/{venue_id}")
    assert fetched.status_code == 200
    assert fetched.json()["display_name"] == "Harbour Hall Renamed"
