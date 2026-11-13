from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from functools import partial
from hashlib import sha3_256
from io import BytesIO
from typing import TYPE_CHECKING, Annotated, BinaryIO, Protocol
from uuid import UUID

import anyio.to_thread
import obstore
from fastapi import Depends, UploadFile
from obstore.store import AzureStore, GCSStore, S3Store
from PIL import Image, ImageOps
from PIL.Image import Resampling
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from quickticket.dependencies.db import AsyncSessionMakerDep
from quickticket.dependencies.state import SettingsDep
from quickticket.dependencies.store import ObjectStoreDep
from quickticket.errors import FileSizeExceeded, ImageAnimationNotAccepted, ImageFormatNotAccepted
from quickticket.models import MimeType, StorageObject, StorageProvider, User

if TYPE_CHECKING:
    from obstore import GetResult

__all__ = (
    "ImageService",
    "ImageServiceDep",
    "get_image_service",
)

# Careful on accepted formats, some are more prone to vulnerabilities
MIME_TYPES_TO_EXTENSIONS = {
    MimeType("image/avif"): "avif",
    MimeType("image/bmp"): "bmp",
    MimeType("image/gif"): "gif",
    MimeType("image/jpeg"): "jpeg",
    MimeType("image/png"): "png",
    MimeType("image/webp"): "webp",
}
ACCEPTED_IMAGE_MIME_TYPES = tuple(MIME_TYPES_TO_EXTENSIONS)
ACCEPTED_IMAGE_FORMATS = tuple(MIME_TYPES_TO_EXTENSIONS.values())
MAX_FILESIZE = 2**20 * 10

log = logging.getLogger(__name__)


def _process_image(file: BinaryIO, *, size: tuple[int, int]) -> tuple[bytes, MimeType]:
    mime_type = MimeType("image/jpeg")
    fmt = MIME_TYPES_TO_EXTENSIONS[mime_type]

    with Image.open(file, formats=ACCEPTED_IMAGE_FORMATS) as image, BytesIO() as f:
        # TODO: strict dimension assertions? minimum size, maximum size
        _check_not_animated(image)

        # https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#resize-relative-to-a-given-size
        resized = ImageOps.contain(image, size, Resampling.BICUBIC)

        # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#jpeg-saving
        resized.save(f, fmt, quality=75, optimize=True, progressive=True)

        return f.getvalue(), mime_type


def _check_not_animated(image: Image.Image) -> None:
    if getattr(image, "is_animated", False):
        raise ImageAnimationNotAccepted


class Entity(Protocol):
    @property
    def id(self) -> UUID | None: ...


@dataclass(kw_only=True, repr=False)
class ImageService:
    make_session: AsyncSessionMakerDep
    settings: SettingsDep
    store: ObjectStoreDep

    async def get(self, obj: StorageObject) -> GetResult:
        return await self.store.get_async(obj.object_key)

    async def get_url(self, obj: StorageObject) -> str:
        assert isinstance(self.store, (AzureStore, GCSStore, S3Store))
        return await obstore.sign_async(
            self.store,
            "GET",
            obj.object_key,
            expires_in=timedelta(minutes=10),
        )

    async def upload_banner(
        self,
        entity: Entity,
        file: UploadFile,
        *,
        user: User,
    ) -> StorageObject:
        base_key = f"banners/{entity.id}"
        size = (2048, 1024)
        return await self._upload(user=user, file=file, base_key=base_key, size=size)

    async def upload_thumbnail(
        self,
        entity: Entity,
        file: UploadFile,
        *,
        user: User,
    ) -> StorageObject:
        base_key = f"thumbnails/{entity.id}"
        size = (512, 512)
        return await self._upload(user=user, file=file, base_key=base_key, size=size)

    async def _upload(
        self,
        *,
        user: User,
        file: UploadFile,
        base_key: str,
        size: tuple[int, int],
    ) -> StorageObject:
        await self._check_file(file)
        await self._check_ratelimit(user)

        image_bytes, mime_type = await anyio.to_thread.run_sync(
            partial(_process_image, file.file, size=size),
        )

        filename = self._calculate_filename(image_bytes, mime_type)
        key = f"{base_key}/{filename}"

        _ = await self.store.put_async(key, image_bytes)

        # Intentionally use a separate session to commit early
        # and avoid rolling back if an exception is raised downstream.
        async with self.make_session.begin() as session:
            obj = StorageObject(
                object_key=key,
                filename=filename,  # TODO: is this redundant? maybe turn into property
                filesize=len(image_bytes),
                mime_type=mime_type,
                provider=await self._get_storage_provider(session),
                account_id=user.id,  # can't set user directly when attached to another session
            )
            session.add(obj)

        return obj

    async def _check_file(self, file: UploadFile) -> None:
        if file.content_type not in ACCEPTED_IMAGE_MIME_TYPES:
            raise ImageFormatNotAccepted(file.content_type, ACCEPTED_IMAGE_MIME_TYPES)
        FileSizeExceeded.raise_if_exceeded(file.size, max_filesize=MAX_FILESIZE)

    async def _check_ratelimit(self, user: User) -> None:
        pass  # TODO: per-user ratelimiting

    @staticmethod
    def _calculate_filename(data: bytes, mime_type: MimeType) -> str:
        ext = MIME_TYPES_TO_EXTENSIONS[mime_type]
        data_hash = sha3_256(data).hexdigest()[:32]
        return f"{data_hash}.{ext}"

    async def _get_storage_provider(self, session: AsyncSession) -> StorageProvider:
        assert self.settings.s3 is not None
        url = str(self.settings.s3.url.get_secret_value())
        region = self.settings.s3.region.get_secret_value()

        # Should this be cached?
        provider = await session.scalar(
            select(StorageProvider).where(
                StorageProvider.endpoint == url,
                StorageProvider.region == region,
            ),
        )

        if provider is None:
            provider = StorageProvider(
                endpoint=url,
                region=region,
                bucket="",  # TODO: is this really needed? bucket goes in url
                cdn_base_url="",  # TODO: add CDN url
            )
            session.add(provider)

        return provider


async def get_image_service(
    make_session: AsyncSessionMakerDep,
    settings: SettingsDep,
    store: ObjectStoreDep,
) -> ImageService:
    return ImageService(make_session=make_session, settings=settings, store=store)


ImageServiceDep = Annotated[ImageService, Depends(get_image_service)]
