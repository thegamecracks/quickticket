from uuid import UUID

import pytest
from httpx2 import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import Address
from tests.conftest import AuthController


@pytest.mark.asyncio
async def test_profile_me(
    auth: AuthController,
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    user = auth.user

    response = await client.get("/api/profile/@me")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 7
    assert UUID(data["account_id"]) == user.id
    assert data["created_at"] is not None
    assert data["display_name"] == "Test User"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"
    assert data["email"] == "test.user@example.com"

    async with make_session() as session:
        address = await session.scalar(select(Address).where(Address.account_id == user.id))

    assert address is not None
    assert data["addresses"] == [
        {
            "address_id": str(address.id),
            "line_1": "123 Test Street",
            "line_2": "Unit 4",
            "city": "Testville",
            "province": "Ontario",
            "postal_code": "A1B 2C3",
        }
    ]
