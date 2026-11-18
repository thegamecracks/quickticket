from io import BytesIO
from uuid import uuid7

import pytest
from fastapi import UploadFile
from fastapi.datastructures import Headers
from PIL import Image
from sqlalchemy import select
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.dependencies.images import (
    MAX_DIMENSIONS,
    ImageService,
    _build_storage_object_upsert,
)
from quickticket.dependencies.store import Store
from quickticket.models import (
    MimeType,
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    StorageObject,
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


@pytest.fixture
def user() -> User:
    return User(
        display_name="Test User",
        first_name="Test",
        last_name="User",
        email="test.user@example.com",
    )


def make_upload_file(data: bytes) -> UploadFile:
    return UploadFile(
        BytesIO(data),
        filename="image.webp",
        size=len(data),
        headers=Headers({"Content-Type": "image/webp"}),
    )


@pytest.fixture
async def venue(make_session: async_sessionmaker[AsyncSession], user: User) -> Venue:
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
        theme="Sports",
        location_name="Test Stadium",
    )

    async with make_session.begin() as session:
        session.add_all([user, organization, member, venue])

    return venue


async def test_image_service_upload_banner(
    make_session: async_sessionmaker[AsyncSession],
    store: Store,
    settings: Settings,
    user: User,
    venue: Venue,
    image: UploadFile,
) -> None:
    images = ImageService(make_session=make_session, settings=settings, store=store)

    obj = await images.upload_banner(venue, image, user=user)
    assert obj.id is not None
    assert obj.storage_provider_id is not None
    assert obj.user_id == user.id
    assert obj.object_key.startswith(f"banners/{venue.id}/")
    assert obj.object_key.endswith(obj.filename)
    assert obj.filesize == 6816
    assert obj.mime_type == MimeType("image/jpeg")
    assert obj.created_at is not None
    assert obj.provider is not None

    result = await store.head_async(obj.object_key)
    assert result["path"] == f"banners/{venue.id}/89027eaa09acace3d55ed283e3007d64.jpeg"
    assert result["size"] == obj.filesize


async def test_image_service_upload_banner_reuses_identical_bytes(
    make_session: async_sessionmaker[AsyncSession],
    store: Store,
    settings: Settings,
    user: User,
    venue: Venue,
    black_image_bytes: bytes,
) -> None:
    images = ImageService(make_session=make_session, settings=settings, store=store)
    other_user = User(
        display_name="Other User",
        first_name="Other",
        last_name="User",
        email="other.user@example.com",
    )
    async with make_session.begin() as session:
        session.add(other_user)

    first = await images.upload_banner(venue, make_upload_file(black_image_bytes), user=user)
    second = await images.upload_banner(
        venue,
        make_upload_file(black_image_bytes),
        user=other_user,
    )

    assert second.id == first.id
    assert second.user_id == user.id
    assert second.object_key == first.object_key

    async with make_session.begin() as session:
        objects = list(
            await session.scalars(
                select(StorageObject).where(StorageObject.object_key == first.object_key),
            ),
        )

    assert len(objects) == 1


def test_storage_object_upsert_unsupported_dialect() -> None:
    with pytest.raises(NotImplementedError, match="mysql"):
        _build_storage_object_upsert("mysql", {})


def test_storage_object_upsert_supports_postgresql() -> None:
    """The Postgres branch is production-only; SQLite-backed tests never reach it."""
    stmt = _build_storage_object_upsert(
        "postgresql",
        {
            "id": uuid7(),
            "storage_provider_id": uuid7(),
            "object_key": "banners/example/image.jpeg",
            "filename": "image.jpeg",
            "filesize": 1,
            "mime_type": MimeType("image/jpeg"),
        },
    )

    compiled = str(stmt.compile(dialect=postgresql.dialect()))
    assert "ON CONFLICT (storage_provider_id, object_key) DO NOTHING" in compiled


def test_max_dimensions_fit_pillow_pixel_limit() -> None:
    # A max-size image must stay under Pillow's decompression bomb threshold,
    # otherwise the pixel backstop rejects images that the limit allows.
    max_pixels = Image.MAX_IMAGE_PIXELS
    assert max_pixels is not None
    assert MAX_DIMENSIONS[0] * MAX_DIMENSIONS[1] <= max_pixels
