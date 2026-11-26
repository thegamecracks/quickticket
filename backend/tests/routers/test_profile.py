from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx2 import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import (
    Address,
    AddressID,
    Organization,
    OrganizationID,
    OrganizationMember,
    OrganizationMemberPermissions,
    User,
    UserID,
)
from tests.conftest import AuthController, isoformat

USER_A_ID = UserID(UUID("11111111-1111-4111-8111-111111111111"))
USER_B_ID = UserID(UUID("22222222-2222-4222-8222-222222222222"))

ADDRESS_A1_ID = AddressID(UUID("00000000-0000-4000-8000-000000000001"))
ADDRESS_A2_ID = AddressID(UUID("00000000-0000-4000-8000-000000000002"))
ADDRESS_B1_ID = AddressID(UUID("00000000-0000-4000-8000-000000000003"))

ORGANIZATION_A_ID = OrganizationID(UUID("00000000-0000-4000-8000-000000000011"))
ORGANIZATION_B_ID = OrganizationID(UUID("00000000-0000-4000-8000-000000000012"))
ORGANIZATION_C_ID = OrganizationID(UUID("00000000-0000-4000-8000-000000000013"))

PROFILE_COLLECTION_PATHS = [
    "/api/profile/@me/addresses",
    "/api/profile/@me/organizations/members",
]


@pytest.fixture
async def user(
    app: FastAPI,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
) -> User:
    assert auth.user is not None

    async with make_session.begin() as session:
        session.add(auth.user)
        auth.user.created_at = datetime(2026, 1, 1, tzinfo=UTC)
        auth.user.email = "profile.user@example.com"
        await session.delete_all(auth.user.addresses)

    return auth.user


@pytest.fixture
async def other_user(make_session: async_sessionmaker[AsyncSession]) -> User:
    other_user = User(
        id=USER_B_ID,
        display_name="Other User",
        first_name="Other",
        last_name="User",
        email="other.user@example.com",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    async with make_session.begin() as session:
        session.add(other_user)
    return other_user


def address_payload(address: Address) -> dict[str, str]:
    """The wire shape of an address, without the ORM-only ``user_id``."""
    return {
        "id": str(address.id),
        "line_1": address.line_1,
        "line_2": address.line_2,
        "city": address.city,
        "province": address.province,
        "postal_code": address.postal_code,
    }


def membership_payload(member: OrganizationMember) -> dict[str, str | int]:
    """The wire shape of an organization membership."""
    return {
        "organization_id": str(member.organization_id),
        "user_id": str(member.user_id),
        "permissions": int(member.permissions),
        "joined_at": isoformat(member.joined_at),
    }


async def seed_addresses(
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    other_user: User,
) -> tuple[Address, Address, Address]:
    """Seed two addresses for the user and one for the other user.

    The insertion order deliberately disagrees with the ID order that the route
    sorts by, so a result without ordering cannot satisfy the assertion.

    """
    address_a2 = Address(
        id=ADDRESS_A2_ID,
        user_id=user.id,
        line_1="2 Second Street",
        line_2="Unit 2",
        city="Testville",
        province="Ontario",
        postal_code="D4E 5F6",
    )
    address_a1 = Address(
        id=ADDRESS_A1_ID,
        user_id=user.id,
        line_1="1 First Street",
        line_2="Unit 1",
        city="Testville",
        province="Ontario",
        postal_code="A1B 2C3",
    )
    other_address = Address(
        id=ADDRESS_B1_ID,
        user_id=other_user.id,
        line_1="3 Third Street",
        line_2="Unit 3",
        city="Otherville",
        province="Quebec",
        postal_code="G7H 8I9",
    )
    async with make_session.begin() as session:
        session.add_all([address_a2, address_a1, other_address])
    return address_a1, address_a2, other_address


async def seed_organization_members(
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    other_user: User,
) -> tuple[OrganizationMember, OrganizationMember, OrganizationMember]:
    """Seed three memberships for the user and one for the other user.

    Returns the user's memberships in the order the route should return them:
    ``joined_at`` ascending, then ``organization_id`` ascending.
    The insertion order deliberately disagrees, so a result without ordering
    cannot satisfy the assertion. The other user's membership shares an
    organization with the user's, so a dropped user filter is visible.

    """
    organizations = [
        Organization(
            id=ORGANIZATION_A_ID,
            display_name="Organization A",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        Organization(
            id=ORGANIZATION_B_ID,
            display_name="Organization B",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        ),
        Organization(
            id=ORGANIZATION_C_ID,
            display_name="Organization C",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        ),
    ]
    membership_late = OrganizationMember(
        organization_id=ORGANIZATION_A_ID,
        user_id=user.id,
        permissions=OrganizationMemberPermissions(0),
        joined_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    membership_org_c = OrganizationMember(
        organization_id=ORGANIZATION_C_ID,
        user_id=user.id,
        permissions=OrganizationMemberPermissions.OWNER,
        joined_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    membership_org_b = OrganizationMember(
        organization_id=ORGANIZATION_B_ID,
        user_id=user.id,
        permissions=OrganizationMemberPermissions.OWNER,
        joined_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    other_membership = OrganizationMember(
        organization_id=ORGANIZATION_A_ID,
        user_id=other_user.id,
        permissions=OrganizationMemberPermissions.OWNER,
        joined_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    async with make_session.begin() as session:
        session.add_all(organizations)
    async with make_session.begin() as session:
        session.add_all([membership_late, membership_org_c, other_membership, membership_org_b])
    return membership_org_b, membership_org_c, membership_late


async def test_profile_me_unauthenticated(
    auth: AuthController,
    client: AsyncClient,
) -> None:
    auth.user = None

    response = await client.get("/api/profile/@me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


async def test_profile_me_omits_related_collections(
    user: User,
    other_user: User,
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    await seed_addresses(make_session, user, other_user)
    await seed_organization_members(make_session, user, other_user)

    response = await client.get("/api/profile/@me")
    assert response.status_code == 200
    assert response.json() == {
        "id": str(user.id),
        "created_at": isoformat(user.created_at),
        "display_name": user.display_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
    }


@pytest.mark.parametrize("path", PROFILE_COLLECTION_PATHS)
async def test_profile_collection_routes_unauthenticated(
    auth: AuthController,
    client: AsyncClient,
    path: str,
) -> None:
    auth.user = None

    response = await client.get(path)
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize("path", PROFILE_COLLECTION_PATHS)
async def test_profile_collection_routes_empty(
    user: User,
    other_user: User,
    client: AsyncClient,
    path: str,
) -> None:
    response = await client.get(path)
    assert response.status_code == 200
    assert response.json() == []


async def test_profile_addresses_returns_only_current_user(
    user: User,
    other_user: User,
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    address_a1, address_a2, _ = await seed_addresses(make_session, user, other_user)

    response = await client.get("/api/profile/@me/addresses")
    assert response.status_code == 200
    assert response.json() == [address_payload(address_a1), address_payload(address_a2)]


async def test_profile_organization_members_returns_only_current_user(
    user: User,
    other_user: User,
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    membership_b, membership_c, membership_a = await seed_organization_members(
        make_session,
        user,
        other_user,
    )

    response = await client.get("/api/profile/@me/organizations/members")
    assert response.status_code == 200
    assert response.json() == [
        membership_payload(membership_b),
        membership_payload(membership_c),
        membership_payload(membership_a),
    ]
