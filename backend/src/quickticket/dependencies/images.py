import logging
from dataclasses import dataclass
from datetime import timedelta
from io import BytesIO
from typing import Annotated, BinaryIO, Protocol
from uuid import UUID

import anyio.to_thread
import obstore
from fastapi import Depends, UploadFile
from obstore.store import AzureStore, GCSStore, S3Store
from PIL import Image, ImageOps
from PIL.Image import Resampling
from pydantic import AwareDatetime, BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from quickticket.dependencies.db import AsyncSessionMakerDep
from quickticket.dependencies.state import SettingsDep
from quickticket.dependencies.store import ObjectStoreDep
from quickticket.errors import FileSizeExceeded, ImageAnimationNotAccepted, ImageFormatNotAccepted
from quickticket.models import MimeType, StorageObject, StorageProvider, User

__all__ = (
    "ImageRead",
    "ImageService",
    "ImageServiceDep",
    "get_image_service",
)

# Careful on accepted formats, some are more prone to vulnerabilities
ACCEPTED_IMAGE_FORMATS = (
    MimeType("image/avif"),
    MimeType("image/bmp"),
    MimeType("image/gif"),
    MimeType("image/jpeg"),
    MimeType("image/png"),
    MimeType("image/webp"),
)

log = logging.getLogger(__name__)


class ImageRead(BaseModel):
    id: UUID
    filename: str
    filesize: str
    mime_type: MimeType
    created_at: AwareDatetime


def _process_banner(file: BinaryIO) -> bytes:
    with Image.open(file, formats=ACCEPTED_IMAGE_FORMATS) as image, BytesIO() as f:
        # TODO: strict dimension assertions? minimum size, maximum size
        _check_not_animated(image)

        # https://pillow.readthedocs.io/en/stable/reference/ImageOps.html#resize-relative-to-a-given-size
        resized = ImageOps.contain(image, (2048, 1024), Resampling.BICUBIC)

        # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#jpeg-saving
        resized.save(f, "jpeg", quality=75, optimize=True, progressive=True)

        return f.getvalue()


def _check_not_animated(image: Image.Image) -> None:
    if getattr(image, "is_animated", False):
        raise ImageAnimationNotAccepted


class BannerEntity(Protocol):
    banner: StorageObject | None

    @property
    def id(self) -> UUID | None: ...


@dataclass(kw_only=True, repr=False)
class ImageService:
    make_session: AsyncSessionMakerDep
    settings: SettingsDep
    store: ObjectStoreDep

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
        entity: BannerEntity,
        file: UploadFile,
        *,
        user: User,
    ) -> StorageObject:
        key_str = f"banners/{entity.id}/"
        await self._check(key_str, user, file)
        mime_type = MimeType(file.content_type)

        image_bytes = await anyio.to_thread.run_sync(_process_banner, file.file)

        # Intentionally use a separate session to commit early
        # and avoid rolling back if an exception is raised downstream.
        async with self.make_session.begin() as session:
            obj = await self._upload(session, key_str, image_bytes, mime_type=mime_type)
            entity.banner = obj
            return obj

    async def _check(
        self,
        key: str,
        user: User,
        file: UploadFile,
        *,
        max_filesize: int = 2**20 * 10,
    ) -> None:
        if not key.endswith("/"):
            raise ValueError("Expected trailing slash in object key")

        if file.content_type not in ACCEPTED_IMAGE_FORMATS:
            raise ImageFormatNotAccepted(file.content_type, ACCEPTED_IMAGE_FORMATS)

        FileSizeExceeded.raise_if_exceeded(file.size, max_filesize=max_filesize)

        # TODO: per-user ratelimiting

    async def _upload(
        self,
        session: AsyncSession,
        key: str,
        data: bytes,
        mime_type: MimeType,
    ) -> StorageObject:
        _, _, filename = key.rpartition("/")
        _ = await self.store.put_async(key, data)
        obj = StorageObject(
            object_key=key,
            filename=filename,
            filesize=len(data),
            mime_type=mime_type,
            provider=await self._get_storage_provider(session),
        )
        session.add(obj)
        return obj

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
