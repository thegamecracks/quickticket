from uuid import UUID

import pytest
from httpx2 import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import (
    Organization,
    OrganizationID,
    OrganizationMember,
    OrganizationMemberPermissions,
    User,
)
from tests.conftest import (
    AuthController,
    DatasetLoader,
    assert_validation_error,
    isoformat,
)
from tests.dataset import Dataset


async def test_get_organizations(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset

    response = await client.get("/api/organizations")
    assert response.status_code == 200
    data = response.json()

    assert set(data) == {"items", "next", "total"}
    assert data["total"] == len(dataset.organizations)
    assert data["next"] is None
    assert len(data["items"]) == len(dataset.organizations)

    organizations = {organization.id: organization for organization in dataset.organizations}
    assert {OrganizationID(UUID(item["id"])) for item in data["items"]} == set(organizations)
    for item in data["items"]:
        organization = organizations[OrganizationID(UUID(item["id"]))]
        assert item == {
            "id": str(organization.id),
            "created_at": isoformat(organization.created_at),
            "display_name": organization.display_name,
        }


async def test_get_organizations_before_filters_total(
    client: AsyncClient,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    ordered = sorted(dataset.organizations, key=lambda org: org.created_at, reverse=True)

    # before is a filter: it excludes the three newest organizations.
    response = await client.get(
        "/api/organizations",
        params={"before": isoformat(ordered[2].created_at)},
    )
    assert response.status_code == 200
    data = response.json()

    assert [org["id"] for org in data["items"]] == [str(org.id) for org in ordered[3:]]
    assert data["next"] is None
    assert data["total"] == len(ordered) - 3


async def test_create_organization(
    auth: AuthController,
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    user = auth.user

    response = await client.post("/api/organizations", json={"display_name": "Test Organization"})
    assert response.status_code == 201
    data = response.json()
    assert response.headers.get_list("location") == [f"https://test/api/organizations/{data['id']}"]

    assert len(data) == 5
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["display_name"] == "Test Organization"
    assert data["venues"] == []
    assert UUID(data["members"][0]["user_id"]) == user.id

    async with make_session.begin() as session:
        member = await session.get(OrganizationMember, (UUID(data["id"]), user.id))
        assert member is not None
        assert member.permissions == OrganizationMemberPermissions.OWNER


async def test_create_organization_one_owner_only(
    auth: AuthController,
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    response = await client.post("/api/organizations", json={"display_name": "First Organization"})
    assert response.status_code == 201
    first = response.json()

    response = await client.post("/api/organizations", json={"display_name": "Second Organization"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Already owns an organization"}

    async with make_session.begin() as session:
        organizations = await session.scalars(select(Organization))
        assert [organization.id for organization in organizations] == [UUID(first["id"])]


async def test_create_organization_rejects_blank_display_name(
    auth: AuthController,
    client: AsyncClient,
) -> None:
    response = await client.post("/api/organizations", json={"display_name": ""})
    assert response.status_code == 422


async def test_create_organization_rejects_overlong_display_name(
    auth: AuthController,
    client: AsyncClient,
) -> None:
    response = await client.post("/api/organizations", json={"display_name": "x" * 129})
    assert response.status_code == 422


async def test_create_organization_rejects_whitespace_only_display_name(
    auth: AuthController,
    client: AsyncClient,
) -> None:
    response = await client.post("/api/organizations", json={"display_name": "   \t\n"})
    assert response.status_code == 422


async def test_create_organization_rejects_too_short_display_name(
    auth: AuthController,
    client: AsyncClient,
) -> None:
    # 2 characters after whitespace stripping.
    response = await client.post("/api/organizations", json={"display_name": " ab "})
    assert response.status_code == 422


async def test_create_organization_rejects_non_printable_display_name(
    auth: AuthController,
    client: AsyncClient,
) -> None:
    # Control characters are removed, leaving fewer than 3 characters.
    response = await client.post("/api/organizations", json={"display_name": "\x00\x1b a"})
    assert response.status_code == 422


async def test_create_organization_strips_whitespace_and_filters_non_printable_characters(
    auth: AuthController,
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    response = await client.post(
        "/api/organizations",
        json={"display_name": "  \u200bMy Org\x00  "},
    )
    assert response.status_code == 201

    data = response.json()
    assert data["display_name"] == "My Org"

    async with make_session() as session:
        organization = await session.scalar(select(Organization))
        assert organization is not None
        assert organization.display_name == "My Org"


async def test_create_organization_rejects_unknown_field(client: AsyncClient) -> None:
    response = await client.post(
        "/api/organizations",
        json={"display_name": "Test Organization", "bogus": "x"},
    )

    assert_validation_error(
        response,
        loc=("body", "bogus"),
        error_type="extra_forbidden",
        msg_contains="Extra inputs are not permitted",
    )


ORGANIZATION_KEYS = frozenset({"created_at", "display_name", "id", "members", "venues"})
"""The keys served by :class:`quickticket.routers.organizations.OrganizationRead`."""

ORGANIZATION_VENUE_KEYS = frozenset(
    {
        "banner",
        "category",
        "created_at",
        "description",
        "display_name",
        "events",
        "id",
        "thumbnail",
    },
)
"""The keys of a venue nested in an :class:`OrganizationRead`."""


def _owner_of_organization(dataset: Dataset, organization: Organization) -> User:
    """Return a user who owns the organization."""
    member = next(
        item for item in dataset.organization_members if item.organization_id == organization.id
    )
    return next(user for user in dataset.users if user.id == member.user_id)


async def test_edit_organization(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    organization = dataset.organizations[0]
    expected_venues = [item for item in dataset.venues if item.organization_id == organization.id]
    expected_members = [
        item for item in dataset.organization_members if item.organization_id == organization.id
    ]
    auth.user = _owner_of_organization(dataset, organization)

    response = await client.patch(
        f"/api/organizations/{organization.id}",
        json={"display_name": "Edited Organization"},
    )
    assert response.status_code == 200
    data = response.json()

    assert set(data) == ORGANIZATION_KEYS
    assert data["id"] == str(organization.id)
    assert data["display_name"] == "Edited Organization"

    # Fields absent from the payload keep their seeded values.
    assert {venue["id"] for venue in data["venues"]} == {str(venue.id) for venue in expected_venues}
    assert all(set(venue) == ORGANIZATION_VENUE_KEYS for venue in data["venues"])
    assert {member["user_id"] for member in data["members"]} == {
        str(member.user_id) for member in expected_members
    }

    fetched = await client.get(f"/api/organizations/{organization.id}")
    assert fetched.status_code == 200
    assert fetched.json() == data


async def test_edit_organization_strips_whitespace_and_filters_non_printable_characters(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    organization = dataset.organizations[0]
    auth.user = _owner_of_organization(dataset, organization)

    response = await client.patch(
        f"/api/organizations/{organization.id}",
        json={"display_name": "  \u200bMy Org\x00  "},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["display_name"] == "My Org"

    fetched = await client.get(f"/api/organizations/{organization.id}")
    assert fetched.status_code == 200
    assert fetched.json() == data


async def test_edit_organization_not_found(client: AsyncClient) -> None:
    response = await client.patch(
        "/api/organizations/00000000-0000-0000-0000-000000000000",
        json={"display_name": "Edited Organization"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


async def test_edit_organization_unauthenticated(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    organization = dataset.organizations[0]
    auth.user = None

    response = await client.patch(
        f"/api/organizations/{organization.id}",
        json={"display_name": "Edited Organization"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


async def test_edit_organization_non_member(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    organization = dataset.organizations[0]
    member_ids = {member.user_id for member in dataset.organization_members}
    auth.user = next(user for user in dataset.users if user.id not in member_ids)

    response = await client.patch(
        f"/api/organizations/{organization.id}",
        json={"display_name": "Edited Organization"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": (f"User ({auth.user.id}) is not a member of organization ({organization.id})"),
    }


async def test_edit_organization_member_without_owner(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    dataset = dataset_loader.dataset
    organization = dataset.organizations[0]
    member = next(
        item for item in dataset.organization_members if item.organization_id == organization.id
    )
    # Downgrade the member before loading so the request authenticates as a
    # member that lacks the OWNER permission.
    member.permissions = OrganizationMemberPermissions(0)
    await dataset_loader.load()
    auth.user = next(user for user in dataset.users if user.id == member.user_id)

    response = await client.patch(
        f"/api/organizations/{organization.id}",
        json={"display_name": "Edited Organization"},
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            f"Organization member ({organization.id}, {auth.user.id}) missing permissions: OWNER"
        ),
    }


async def test_edit_organization_no_fields(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    organization = dataset.organizations[0]
    auth.user = _owner_of_organization(dataset, organization)

    response = await client.patch(f"/api/organizations/{organization.id}", json={})

    assert response.status_code == 400
    assert response.json() == {"detail": "No fields to update"}


@pytest.mark.parametrize("display_name", ["", "   \t\n", " ab ", "x" * 129])
async def test_edit_organization_rejects_invalid_display_name(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    display_name: str,
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    organization = dataset.organizations[0]
    auth.user = _owner_of_organization(dataset, organization)

    response = await client.patch(
        f"/api/organizations/{organization.id}",
        json={"display_name": display_name},
    )

    assert response.status_code == 422
    locations = {tuple(error["loc"]) for error in response.json()["detail"]}
    assert ("body", "display_name") in locations


@pytest.mark.parametrize(
    "changes",
    [
        {"bogus": "x"},
        {"display_name": "Changed", "bogus": "x"},
    ],
)
async def test_edit_organization_rejects_unknown_field(
    client: AsyncClient,
    auth: AuthController,
    dataset_loader: DatasetLoader,
    changes: dict[str, object],
) -> None:
    await dataset_loader.load()
    dataset = dataset_loader.dataset
    organization = dataset.organizations[0]
    auth.user = _owner_of_organization(dataset, organization)

    response = await client.patch(f"/api/organizations/{organization.id}", json=changes)

    assert_validation_error(
        response,
        loc=("body", "bogus"),
        error_type="extra_forbidden",
        msg_contains="Extra inputs are not permitted",
    )

    fetched = await client.get(f"/api/organizations/{organization.id}")
    assert fetched.status_code == 200
    assert fetched.json()["display_name"] == organization.display_name
