from uuid import UUID

import pytest
from httpx2 import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import (
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
)
from tests.conftest import AuthController


@pytest.mark.asyncio
async def test_create_organization(
    auth: AuthController,
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    assert auth.user is not None
    user = auth.user

    response = await client.post("/api/organizations", json={"display_name": "Test Organization"})
    response.raise_for_status()
    data = response.json()

    assert len(data) == 5
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["display_name"] == "Test Organization"
    assert data["venues"] == []
    assert UUID(data["members"][0]["account_id"]) == user.id

    async with make_session() as session, session.begin():
        member = await session.get(OrganizationMember, (UUID(data["id"]), user.id))
        assert member is not None
        assert member.permissions == OrganizationMemberPermissions.ADMINISTRATOR


@pytest.mark.asyncio
async def test_create_organization_one_owner_only(
    auth: AuthController,
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    response = await client.post("/api/organizations", json={"display_name": "First Organization"})
    response.raise_for_status()
    first = response.json()

    response = await client.post("/api/organizations", json={"display_name": "Second Organization"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Already owns an organization"}

    async with make_session() as session, session.begin():
        organizations = await session.scalars(select(Organization))
        assert [organization.id for organization in organizations] == [UUID(first["id"])]


@pytest.mark.asyncio
async def test_create_organization_rejects_blank_display_name(
    auth: AuthController,
    client: AsyncClient,
) -> None:
    response = await client.post("/api/organizations", json={"display_name": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_organization_rejects_overlong_display_name(
    auth: AuthController,
    client: AsyncClient,
) -> None:
    response = await client.post("/api/organizations", json={"display_name": "x" * 129})
    assert response.status_code == 422
