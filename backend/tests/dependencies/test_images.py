from io import BytesIO

import pytest
import pytest_asyncio
from fastapi import UploadFile
from fastapi.datastructures import Headers
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.dependencies.images import ImageService
from quickticket.dependencies.store import Store
from quickticket.models import (
    MimeType,
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    User,
    Venue,
)
from quickticket.settings import S3Settings, Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        _env_file=None,
        s3=S3Settings(
            url="memory:///",
            region="us-east-1",
            access_key="test-access-key",
            secret_key="test-secret-key",  # noqa: S106
        ),
    )


@pytest.fixture(scope="session")
def black_image_bytes() -> bytes:
    # Should be small, ~162 bytes
    image = Image.new("L", (256, 128))
    with BytesIO() as f:
        image.save(f, "webp", quality=0, method=0)
        return f.getvalue()


@pytest.fixture
def black_image_file(black_image_bytes: bytes) -> UploadFile:
    return UploadFile(
        BytesIO(black_image_bytes),
        size=len(black_image_bytes),
        headers=Headers({"Content-Type": "image/webp"}),
    )


@pytest.fixture
def user() -> User:
    return User(
        display_name="Test User",
        first_name="Test",
        last_name="User",
        email="test.user@example.com",
    )


@pytest_asyncio.fixture
async def venue(make_session: async_sessionmaker[AsyncSession], user: User) -> Venue:
    organization = Organization(display_name="Test Organization")
    member = OrganizationMember(
        organization_id=organization.id,
        account_id=user.id,
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
        session.add_all([user, organization, member, venue])

    return venue


@pytest.mark.asyncio
async def test_image_service_upload_banner(
    make_session: async_sessionmaker[AsyncSession],
    store: Store,
    settings: Settings,
    user: User,
    venue: Venue,
    black_image_file: UploadFile,
) -> None:
    images = ImageService(make_session=make_session, settings=settings, store=store)

    obj = await images.upload_banner(venue, black_image_file, user=user)
    assert obj.id is not None
    assert obj.storage_provider_id is not None
    assert obj.account_id == user.id
    assert obj.object_key.startswith(f"banners/{venue.id}/")
    assert obj.object_key.endswith(obj.filename)
    assert obj.filesize == 12836
    assert obj.mime_type == MimeType("image/jpeg")
    assert obj.created_at is not None
    assert obj.provider is not None
    assert obj.user is user

    result = await store.head_async(obj.object_key)
    assert result["path"] == f"banners/{venue.id}/dba2914f55714cfeaa1ff877800f0cce.jpeg"
    assert result["size"] == obj.filesize
