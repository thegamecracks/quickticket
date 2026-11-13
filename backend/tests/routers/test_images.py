from uuid import UUID

import pytest
import pytest_asyncio
from fastapi import UploadFile
from httpx2 import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from quickticket.models import (
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    StorageObjectID,
    Venue,
)
from tests.conftest import AuthController


@pytest_asyncio.fixture
async def venue(auth: AuthController, make_session: async_sessionmaker[AsyncSession]) -> Venue:
    assert auth.user is not None
    organization = Organization(display_name="Test Organization")
    member = OrganizationMember(
        organization_id=organization.id,
        account_id=auth.user.id,
        permissions=OrganizationMemberPermissions.ADMINISTRATOR,
    )
    venue = Venue(
        organization_id=organization.id,
        display_name="Test Venue",
        description="A venue for testing.",
        theme="Sports",
        location_name="Test Stadium",
    )

    async with make_session.begin() as session:
        session.add_all([organization, member, venue])

    return venue


@pytest.mark.asyncio
async def test_set_banner(
    client: AsyncClient,
    venue: Venue,
    make_session: async_sessionmaker[AsyncSession],
    image: UploadFile,
) -> None:
    file = (image.filename, image.file, image.content_type)
    response = await client.put(
        f"/api/venues/{venue.id}/banner",
        files={"file": file},
    )
    assert response.status_code == 200
    data = response.json()

    assert set(data) == {"id", "filename", "filesize", "mime_type", "created_at"}
    assert data["id"] is not None
    assert data["filename"] == "dba2914f55714cfeaa1ff877800f0cce.jpeg"
    assert data["filesize"] == 12836
    assert data["mime_type"] == "image/jpeg"
    assert data["created_at"] is not None

    async with make_session.begin() as session:
        stored = await session.get(Venue, venue.id, options=[selectinload(Venue.banner)])
        assert stored is not None
        assert stored.banner is not None
        assert stored.banner.id == StorageObjectID(UUID(data["id"]))
