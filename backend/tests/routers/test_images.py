from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from fastapi import FastAPI, Request, UploadFile
from fastapi.datastructures import Headers
from httpx2 import AsyncClient, Response
from limits import RateLimitItem, parse
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload
from starlette.routing import get_route_path

from quickticket.dependencies.auth import OptionalUserDep
from quickticket.dependencies.images import ImageService
from quickticket.dependencies.ratelimits import get_request_limits
from quickticket.dependencies.store import Store
from quickticket.models import (
    Event,
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    StorageObject,
    StorageObjectID,
    User,
    Venue,
)
from tests.conftest import AuthController

ENTITY_CLASSES = pytest.mark.parametrize("entity_cls", [Venue, Event], ids=["venue", "event"])
IMAGE_KINDS = pytest.mark.parametrize("kind", ["banner", "thumbnail"])
NOT_FOUND_ID = UUID("00000000-0000-0000-0000-000000000000")

# The black image fixture is processed (and resized) by ImageService.
EXPECTED_IMAGES = {
    "banner": ("84f56137df1187ce507275dca3e850a9.jpeg", 12836),
    "thumbnail": ("7f23efabb618aefc7f768efa37840fa8.jpeg", 1373),
}


@dataclass(kw_only=True)
class SeededEntity:
    entity: Venue | Event
    organization: Organization


def make_upload_file(
    data: bytes,
    *,
    filename: str = "image.webp",
    content_type: str = "image/webp",
) -> UploadFile:
    return UploadFile(
        BytesIO(data),
        filename=filename,
        size=len(data),
        headers=Headers({"Content-Type": content_type}),
    )


def entity_image_url(entity: Venue | Event, kind: str) -> str:
    return f"/api/{type(entity).__tablename__}s/{entity.id}/{kind}"


async def put_image(
    client: AsyncClient,
    entity: Venue | Event,
    kind: str,
    image: UploadFile,
) -> Response:
    file = (image.filename, image.file, image.content_type)
    return await client.put(entity_image_url(entity, kind), files={"file": file})


async def seed_entity(
    make_session: async_sessionmaker[AsyncSession],
    entity_cls: type[Venue | Event],
    user: User,
    *,
    permissions: OrganizationMemberPermissions | None = (
        OrganizationMemberPermissions.ADMINISTRATOR
    ),
) -> SeededEntity:
    """Create an organization and one entity owned by it.

    :param permissions:
        The authenticated user's permissions in the organization.
        Pass ``None`` to leave the user out of the organization entirely.
    """
    organization = Organization(display_name="Test Organization")
    venue = Venue(
        organization_id=organization.id,
        display_name="Test Venue",
        description="A venue for testing.",
        theme="Sports",
        location_name="Test Stadium",
    )
    models: list[Any] = [organization, venue]

    if permissions is not None:
        models.append(
            OrganizationMember(
                organization_id=organization.id,
                account_id=user.id,
                permissions=permissions,
            ),
        )

    entity: Venue | Event
    if entity_cls is Venue:
        entity = venue
    else:
        entity = Event(
            venue_id=venue.id,
            display_name="Test Event",
            description="An event for testing.",
            theme="Sports",
            starts_at=datetime.now(UTC) + timedelta(days=1),
            ends_at=datetime.now(UTC) + timedelta(days=2),
        )
        models.append(entity)

    async with make_session.begin() as session:
        session.add_all(models)

    return SeededEntity(entity=entity, organization=organization)


async def get_stored_image(
    make_session: async_sessionmaker[AsyncSession],
    entity_cls: type[Venue | Event],
    entity_id: UUID,
    kind: str,
) -> StorageObject | None:
    async with make_session.begin() as session:
        stored = await session.get(
            entity_cls,
            entity_id,
            options=[selectinload(getattr(entity_cls, kind))],
        )
        assert stored is not None
        return getattr(stored, kind)


@pytest.fixture
def user(auth: AuthController) -> User:
    assert auth.user is not None
    return auth.user


@pytest.fixture
def alt_image() -> UploadFile:
    """An image whose bytes differ from the shared image fixture."""
    with BytesIO() as f:
        Image.new("L", (256, 128), color=255).save(f, "webp", quality=0, method=0)
        return make_upload_file(f.getvalue(), filename="alt.webp")


@pytest.fixture
def override_image_limits(
    app: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[str, str], None]:
    """Replace image mutation limits with a tiny limit for a test."""

    def install(method: str, limit: str) -> None:
        async def override(
            request: Request,
            user: OptionalUserDep,
        ) -> Sequence[RateLimitItem]:
            path = get_route_path(request.scope)
            if request.method == method and path.endswith(("/banner", "/thumbnail")):
                return [parse(limit)]
            return await get_request_limits(request, user)

        monkeypatch.setitem(app.dependency_overrides, get_request_limits, override)

    return install


@pytest.fixture
def animated_image() -> UploadFile:
    frames = [Image.new("L", (64, 64), color=color) for color in (0, 255)]
    with BytesIO() as f:
        frames[0].save(
            f,
            "webp",
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0,
        )
        return make_upload_file(f.getvalue(), filename="animated.webp")


@pytest.fixture
def get_url_mock(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Fake signed URLs; the real implementation requires a cloud object store."""
    mock = AsyncMock(return_value="https://example.com/image.jpeg")
    monkeypatch.setattr(ImageService, "get_url", mock)
    return mock


@pytest.mark.asyncio
@ENTITY_CLASSES
@IMAGE_KINDS
async def test_set_image(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    store: Store,
    user: User,
    entity_cls: type[Venue | Event],
    kind: str,
    image: UploadFile,
) -> None:
    seeded = await seed_entity(make_session, entity_cls, user)

    response = await put_image(client, seeded.entity, kind, image)
    assert response.status_code == 200
    data = response.json()

    filename, filesize = EXPECTED_IMAGES[kind]
    assert set(data) == {"id", "filename", "filesize", "mime_type", "created_at"}
    assert data["id"] is not None
    assert data["filename"] == filename
    assert data["filesize"] == filesize
    assert data["mime_type"] == "image/jpeg"
    assert data["created_at"] is not None

    stored = await get_stored_image(make_session, entity_cls, seeded.entity.id, kind)
    assert stored is not None
    assert stored.id == StorageObjectID(UUID(data["id"]))
    assert stored.account_id == user.id
    assert stored.filesize == filesize

    head = await store.head_async(f"{kind}s/{seeded.entity.id}/{filename}")
    assert head["size"] == filesize


@pytest.mark.asyncio
@ENTITY_CLASSES
@IMAGE_KINDS
async def test_get_image(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    entity_cls: type[Venue | Event],
    kind: str,
    image: UploadFile,
    get_url_mock: AsyncMock,
) -> None:
    seeded = await seed_entity(make_session, entity_cls, user)

    put_response = await put_image(client, seeded.entity, kind, image)
    assert put_response.status_code == 200

    response = await client.get(entity_image_url(seeded.entity, kind))
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/image.jpeg"

    assert get_url_mock.await_args is not None
    (stored,) = get_url_mock.await_args.args
    assert stored.id == StorageObjectID(UUID(put_response.json()["id"]))


@pytest.mark.asyncio
@ENTITY_CLASSES
@IMAGE_KINDS
async def test_get_image_not_set(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    entity_cls: type[Venue | Event],
    kind: str,
) -> None:
    seeded = await seed_entity(make_session, entity_cls, user)

    response = await client.get(entity_image_url(seeded.entity, kind))
    assert response.status_code == 404
    assert response.json() is None


@pytest.mark.asyncio
async def test_replace_image(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    image: UploadFile,
    alt_image: UploadFile,
) -> None:
    seeded = await seed_entity(make_session, Venue, user)

    first = await put_image(client, seeded.entity, "banner", image)
    second = await put_image(client, seeded.entity, "banner", alt_image)
    assert first.status_code == 200
    assert second.status_code == 200
    first_data, second_data = first.json(), second.json()
    assert first_data["id"] != second_data["id"]
    assert first_data["filename"] != second_data["filename"]

    stored = await get_stored_image(make_session, Venue, seeded.entity.id, "banner")
    assert stored is not None
    assert stored.id == StorageObjectID(UUID(second_data["id"]))


@pytest.mark.asyncio
async def test_replace_image_identical_bytes(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    black_image_bytes: bytes,
) -> None:
    """Uploading identical bytes reuses the existing StorageObject."""
    seeded = await seed_entity(make_session, Venue, user)

    first = await put_image(client, seeded.entity, "banner", make_upload_file(black_image_bytes))
    second = await put_image(client, seeded.entity, "banner", make_upload_file(black_image_bytes))
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()

    async with make_session.begin() as session:
        objects = list(await session.scalars(select(StorageObject).order_by(StorageObject.id)))

    assert len(objects) == 1
    assert objects[0].id == StorageObjectID(UUID(second.json()["id"]))


@pytest.mark.asyncio
@ENTITY_CLASSES
@IMAGE_KINDS
async def test_get_image_entity_not_found(
    client: AsyncClient,
    entity_cls: type[Venue | Event],
    kind: str,
) -> None:
    response = await client.get(f"/api/{entity_cls.__tablename__}s/{NOT_FOUND_ID}/{kind}")
    assert response.status_code == 400
    assert response.json() == {
        "detail": f"{entity_cls.__name__} not found: {NOT_FOUND_ID}",
    }


@pytest.mark.asyncio
@ENTITY_CLASSES
@IMAGE_KINDS
async def test_delete_image(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    store: Store,
    user: User,
    entity_cls: type[Venue | Event],
    kind: str,
    image: UploadFile,
) -> None:
    seeded = await seed_entity(make_session, entity_cls, user)
    put_response = await put_image(client, seeded.entity, kind, image)
    assert put_response.status_code == 200

    stored = await get_stored_image(make_session, entity_cls, seeded.entity.id, kind)
    assert stored is not None
    object_id = stored.id
    object_key = stored.object_key

    response = await client.delete(entity_image_url(seeded.entity, kind))
    assert response.status_code == 204
    assert response.content == b""

    with pytest.raises(FileNotFoundError):
        await store.head_async(object_key)

    async with make_session.begin() as session:
        deleted = await session.get(StorageObject, object_id)
        entity = await session.get(entity_cls, seeded.entity.id)
    assert deleted is None
    assert entity is not None
    assert getattr(entity, f"{kind}_id") is None

    stored = await get_stored_image(make_session, entity_cls, seeded.entity.id, kind)
    assert stored is None

    response = await client.get(entity_image_url(seeded.entity, kind))
    assert response.status_code == 404
    assert response.json() is None

    response = await client.delete(entity_image_url(seeded.entity, kind))
    assert response.status_code == 404
    assert response.json() == {"detail": "Image not set"}


@pytest.mark.asyncio
async def test_delete_image_preserves_other_image(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    store: Store,
    user: User,
    image: UploadFile,
    alt_image: UploadFile,
) -> None:
    seeded = await seed_entity(make_session, Venue, user)

    banner_response = await put_image(client, seeded.entity, "banner", image)
    thumbnail_response = await put_image(client, seeded.entity, "thumbnail", alt_image)
    assert banner_response.status_code == 200
    assert thumbnail_response.status_code == 200

    banner = await get_stored_image(make_session, Venue, seeded.entity.id, "banner")
    thumbnail = await get_stored_image(make_session, Venue, seeded.entity.id, "thumbnail")
    assert banner is not None
    assert thumbnail is not None
    thumbnail_id = thumbnail.id
    thumbnail_key = thumbnail.object_key

    response = await client.delete(entity_image_url(seeded.entity, "banner"))
    assert response.status_code == 204

    with pytest.raises(FileNotFoundError):
        await store.head_async(banner.object_key)

    async with make_session.begin() as session:
        deleted = await session.get(StorageObject, banner.id)
        remaining = await session.get(StorageObject, thumbnail_id)
        entity = await session.get(Venue, seeded.entity.id)
    assert deleted is None
    assert remaining is not None
    assert entity is not None
    assert entity.banner_id is None
    assert entity.thumbnail_id == thumbnail_id

    head = await store.head_async(thumbnail_key)
    assert head["size"] == thumbnail.filesize
    stored = await get_stored_image(make_session, Venue, seeded.entity.id, "thumbnail")
    assert stored is not None
    assert stored.id == thumbnail_id


@pytest.mark.asyncio
async def test_delete_image_store_failure(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    store: Store,
    user: User,
    image: UploadFile,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = await seed_entity(make_session, Venue, user)
    put_response = await put_image(client, seeded.entity, "banner", image)
    assert put_response.status_code == 200

    stored = await get_stored_image(make_session, Venue, seeded.entity.id, "banner")
    assert stored is not None
    object_id = stored.id
    object_key = stored.object_key

    monkeypatch.setattr(store, "delete_async", AsyncMock(side_effect=FileNotFoundError))

    with pytest.raises(FileNotFoundError):
        await client.delete(entity_image_url(seeded.entity, "banner"))

    async with make_session.begin() as session:
        row = await session.get(StorageObject, object_id)
        entity = await session.get(Venue, seeded.entity.id)
    assert row is not None
    assert row.id == object_id
    assert entity is not None
    assert entity.banner_id == object_id

    head = await store.head_async(object_key)
    assert head["size"] == stored.filesize


@pytest.mark.asyncio
@IMAGE_KINDS
async def test_delete_image_not_set(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    kind: str,
) -> None:
    seeded = await seed_entity(make_session, Venue, user)

    response = await client.delete(entity_image_url(seeded.entity, kind))
    assert response.status_code == 404
    assert response.json() == {"detail": "Image not set"}


@pytest.mark.asyncio
@ENTITY_CLASSES
@IMAGE_KINDS
async def test_delete_image_entity_not_found(
    client: AsyncClient,
    entity_cls: type[Venue | Event],
    kind: str,
) -> None:
    response = await client.delete(f"/api/{entity_cls.__tablename__}s/{NOT_FOUND_ID}/{kind}")
    assert response.status_code == 400
    assert response.json() == {
        "detail": f"{entity_cls.__name__} not found: {NOT_FOUND_ID}",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("entity_cls", "kind"),
    [(Venue, "banner"), (Event, "thumbnail")],
    ids=["venue-banner", "event-thumbnail"],
)
async def test_set_image_unauthenticated(
    client: AsyncClient,
    auth: AuthController,
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    entity_cls: type[Venue | Event],
    kind: str,
    image: UploadFile,
) -> None:
    seeded = await seed_entity(make_session, entity_cls, user)
    auth.user = None

    response = await put_image(client, seeded.entity, kind, image)
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
@ENTITY_CLASSES
async def test_set_image_non_member(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    entity_cls: type[Venue | Event],
    image: UploadFile,
) -> None:
    seeded = await seed_entity(make_session, entity_cls, user, permissions=None)

    response = await put_image(client, seeded.entity, "banner", image)
    assert response.status_code == 403
    assert response.json() == {
        "detail": f"User ({user.id}) is not a member of organization ({seeded.organization.id})",
    }


@pytest.mark.asyncio
@ENTITY_CLASSES
async def test_set_image_insufficient_permissions(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    entity_cls: type[Venue | Event],
    image: UploadFile,
) -> None:
    seeded = await seed_entity(
        make_session,
        entity_cls,
        user,
        permissions=OrganizationMemberPermissions(0),
    )

    response = await put_image(client, seeded.entity, "banner", image)
    assert response.status_code == 403
    assert response.json() == {
        "detail": (
            f"Organization member ({seeded.organization.id}, {user.id}) "
            "missing permissions: ADMINISTRATOR"
        ),
    }


@pytest.mark.asyncio
async def test_set_image_forbidden_does_not_upload(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    store: Store,
    user: User,
    image: UploadFile,
) -> None:
    seeded = await seed_entity(make_session, Venue, user, permissions=None)

    response = await put_image(client, seeded.entity, "banner", image)
    assert response.status_code == 403

    async with make_session.begin() as session:
        count = await session.scalar(select(func.count()).select_from(StorageObject))
    assert count == 0
    assert [batch async for batch in store.list_async()] == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("entity_cls", "kind"),
    [(Venue, "banner"), (Event, "thumbnail")],
    ids=["venue-banner", "event-thumbnail"],
)
async def test_set_image_entity_not_found(
    client: AsyncClient,
    entity_cls: type[Venue | Event],
    kind: str,
    image: UploadFile,
) -> None:
    file = (image.filename, image.file, image.content_type)
    response = await client.put(
        f"/api/{entity_cls.__tablename__}s/{NOT_FOUND_ID}/{kind}",
        files={"file": file},
    )
    assert response.status_code == 400
    assert response.json() == {
        "detail": f"{entity_cls.__name__} not found: {NOT_FOUND_ID}",
    }


@pytest.mark.asyncio
async def test_set_image_invalid_content_type(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    user: User,
) -> None:
    seeded = await seed_entity(make_session, Venue, user)
    not_an_image = make_upload_file(
        b"not an image",
        filename="notes.txt",
        content_type="text/plain",
    )

    response = await put_image(client, seeded.entity, "banner", not_an_image)
    assert response.status_code == 415
    assert response.json() == {"detail": "Image format not accepted: text/plain"}


@pytest.mark.asyncio
async def test_set_image_oversized(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    image: UploadFile,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = await seed_entity(make_session, Venue, user)
    monkeypatch.setattr("quickticket.dependencies.images.MAX_FILESIZE", 100)
    assert image.size is not None

    response = await put_image(client, seeded.entity, "banner", image)
    assert response.status_code == 400
    assert response.json() == {
        "detail": f"File size exceeded: {image.size:,d}B > 100B",
    }


@pytest.mark.asyncio
async def test_set_image_animated(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    animated_image: UploadFile,
) -> None:
    seeded = await seed_entity(make_session, Venue, user)

    response = await put_image(client, seeded.entity, "banner", animated_image)
    assert response.status_code == 400
    assert response.json() == {"detail": "Animated image not accepted"}


@pytest.mark.asyncio
async def test_set_image_ratelimited(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    image: UploadFile,
    alt_image: UploadFile,
    override_image_limits: Callable[[str, str], None],
) -> None:
    seeded = await seed_entity(make_session, Venue, user)
    override_image_limits("PUT", "1/minute")

    first = await put_image(client, seeded.entity, "banner", image)
    assert first.status_code == 200
    assert first.headers["x-ratelimit-limit"] == "1"
    assert first.headers["x-ratelimit-remaining"] == "1"

    second = await put_image(client, seeded.entity, "banner", alt_image)
    assert second.status_code == 429
    assert second.headers["x-ratelimit-limit"] == "1"
    assert second.headers["x-ratelimit-remaining"] == "0"
    assert second.headers["retry-after"] == second.headers["x-ratelimit-reset-after"]
    assert second.json()["detail"].startswith("You are currently ratelimited for ")

    async with make_session.begin() as session:
        count = await session.scalar(select(func.count()).select_from(StorageObject))
    assert count == 1


@pytest.mark.asyncio
async def test_failed_set_image_counts_towards_ratelimit(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    image: UploadFile,
    override_image_limits: Callable[[str, str], None],
) -> None:
    seeded = await seed_entity(make_session, Venue, user)
    override_image_limits("PUT", "1/minute")
    not_an_image = make_upload_file(
        b"not an image",
        filename="notes.txt",
        content_type="text/plain",
    )

    failed = await put_image(client, seeded.entity, "banner", not_an_image)
    assert failed.status_code == 415

    limited = await put_image(client, seeded.entity, "banner", image)
    assert limited.status_code == 429


@pytest.mark.asyncio
async def test_delete_image_ratelimited(
    client: AsyncClient,
    make_session: async_sessionmaker[AsyncSession],
    store: Store,
    user: User,
    image: UploadFile,
    override_image_limits: Callable[[str, str], None],
) -> None:
    seeded = await seed_entity(make_session, Venue, user)
    put_response = await put_image(client, seeded.entity, "banner", image)
    assert put_response.status_code == 200

    stored = await get_stored_image(make_session, Venue, seeded.entity.id, "banner")
    assert stored is not None
    object_id = stored.id
    object_key = stored.object_key

    override_image_limits("DELETE", "1/minute")

    first = await client.delete(entity_image_url(seeded.entity, "banner"))
    assert first.status_code == 204
    assert first.headers["x-ratelimit-limit"] == "1"
    assert first.headers["x-ratelimit-remaining"] == "1"

    with pytest.raises(FileNotFoundError):
        await store.head_async(object_key)

    second = await client.delete(entity_image_url(seeded.entity, "banner"))
    assert second.status_code == 429
    assert second.headers["x-ratelimit-limit"] == "1"

    with pytest.raises(FileNotFoundError):
        await store.head_async(object_key)

    async with make_session.begin() as session:
        row = await session.get(StorageObject, object_id)
    assert row is None

    stored = await get_stored_image(make_session, Venue, seeded.entity.id, "banner")
    assert stored is None
