from datetime import UTC, datetime
from uuid import UUID

import pytest
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


@pytest.mark.asyncio
async def test_profile_me_unauthenticated(
    auth: AuthController,
    client: AsyncClient,
) -> None:
    auth.user = None

    response = await client.get("/api/profile/@me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_profile_me_plain_user(
    auth: AuthController,
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    user = auth.user = User(
        id=USER_A_ID,
        display_name="Plain User",
        first_name="Plain",
        last_name="User",
        email="plain.user@example.com",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    async with make_session.begin() as session:
        session.add_all([user])

    response = await client.get("/api/profile/@me")
    assert response.status_code == 200
    assert response.json() == {
        "id": str(user.id),
        "created_at": isoformat(user.created_at),
        "display_name": "Plain User",
        "first_name": "Plain",
        "last_name": "User",
        "email": "plain.user@example.com",
        "addresses": [],
        "organization_members": [],
    }


@pytest.mark.asyncio
async def test_profile_me_with_addresses(
    auth: AuthController,
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    user = auth.user = User(
        id=USER_A_ID,
        display_name="Address User",
        first_name="Address",
        last_name="User",
        email="address.user@example.com",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    other_user = User(
        id=USER_B_ID,
        display_name="Other User",
        first_name="Other",
        last_name="User",
        email="other.user@example.com",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    address_1 = Address(
        id=ADDRESS_A1_ID,
        account_id=user.id,
        line_1="1 First Street",
        line_2="Unit 1",
        city="Testville",
        province="Ontario",
        postal_code="A1B 2C3",
    )
    address_2 = Address(
        id=ADDRESS_A2_ID,
        account_id=user.id,
        line_1="2 Second Street",
        line_2="Unit 2",
        city="Testville",
        province="Ontario",
        postal_code="D4E 5F6",
    )
    other_address = Address(
        id=ADDRESS_B1_ID,
        account_id=other_user.id,
        line_1="3 Third Street",
        line_2="Unit 3",
        city="Otherville",
        province="Quebec",
        postal_code="G7H 8I9",
    )
    async with make_session.begin() as session:
        session.add_all([user, other_user, address_1, address_2, other_address])

    response = await client.get("/api/profile/@me")
    assert response.status_code == 200
    assert response.json() == {
        "id": str(user.id),
        "created_at": isoformat(user.created_at),
        "display_name": "Address User",
        "first_name": "Address",
        "last_name": "User",
        "email": "address.user@example.com",
        "addresses": [
            {
                "id": str(address_1.id),
                "line_1": "1 First Street",
                "line_2": "Unit 1",
                "city": "Testville",
                "province": "Ontario",
                "postal_code": "A1B 2C3",
            },
            {
                "id": str(address_2.id),
                "line_1": "2 Second Street",
                "line_2": "Unit 2",
                "city": "Testville",
                "province": "Ontario",
                "postal_code": "D4E 5F6",
            },
        ],
        "organization_members": [],
    }


@pytest.mark.asyncio
async def test_profile_me_with_organization_memberships(
    auth: AuthController,
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    user = auth.user = User(
        id=USER_A_ID,
        display_name="Member User",
        first_name="Member",
        last_name="User",
        email="member.user@example.com",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    other_user = User(
        id=USER_B_ID,
        display_name="Other User",
        first_name="Other",
        last_name="User",
        email="other.user@example.com",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    organization_1 = Organization(
        id=ORGANIZATION_A_ID,
        display_name="Organization One",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    organization_2 = Organization(
        id=ORGANIZATION_B_ID,
        display_name="Organization Two",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    membership_1 = OrganizationMember(
        organization_id=organization_1.id,
        account_id=user.id,
        permissions=OrganizationMemberPermissions.ADMINISTRATOR,
        joined_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    membership_2 = OrganizationMember(
        organization_id=organization_2.id,
        account_id=user.id,
        permissions=OrganizationMemberPermissions(0),
        joined_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    other_membership = OrganizationMember(
        organization_id=organization_1.id,
        account_id=other_user.id,
        permissions=OrganizationMemberPermissions.ADMINISTRATOR,
        joined_at=datetime(2026, 1, 3, tzinfo=UTC),
    )
    async with make_session.begin() as session:
        session.add_all([user, other_user, organization_1, organization_2])
        session.add_all([membership_1, membership_2, other_membership])

    response = await client.get("/api/profile/@me")
    assert response.status_code == 200
    assert response.json() == {
        "id": str(user.id),
        "created_at": isoformat(user.created_at),
        "display_name": "Member User",
        "first_name": "Member",
        "last_name": "User",
        "email": "member.user@example.com",
        "addresses": [],
        "organization_members": [
            {
                "organization_id": str(membership_1.organization_id),
                "account_id": str(membership_1.account_id),
                "permissions": int(membership_1.permissions),
                "joined_at": isoformat(membership_1.joined_at),
            },
            {
                "organization_id": str(membership_2.organization_id),
                "account_id": str(membership_2.account_id),
                "permissions": int(membership_2.permissions),
                "joined_at": isoformat(membership_2.joined_at),
            },
        ],
    }
