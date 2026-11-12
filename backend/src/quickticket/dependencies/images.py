import logging
from dataclasses import dataclass
from functools import partial
from typing import Annotated, BinaryIO
from uuid import UUID

import anyio.to_thread
from fastapi import Depends, UploadFile
from PIL import Image
from pydantic import AwareDatetime, BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from quickticket.dependencies.db import AsyncSessionMakerDep
from quickticket.dependencies.state import SettingsDep
from quickticket.dependencies.store import ObjectStoreDep
from quickticket.errors import FileSizeExceeded, ImageFormatNotAccepted
from quickticket.models import StorageObject, StorageProvider, User

__all__ = (
    "ImageRead",
    "ImageService",
    "ImageServiceDep",
    "get_image_service",
)

# Careful on accepted formats, some are more prone to vulnerabilities
ACCEPTED_IMAGE_FORMATS = (
    "image/avif",
    "image/bmp",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
)

log = logging.getLogger(__name__)


class ImageRead(BaseModel):
    id: UUID
    object_key: str
    filename: str
    filesize: str
    mime_type: str
    created_at: AwareDatetime


def _process_image(file: BinaryIO, *, content_type: str) -> bytes:
    with Image.open(file, formats=ACCEPTED_IMAGE_FORMATS) as image:
        # image.load()
        # TODO: forbid animated images
        raise NotImplementedError(image)  # TODO: resize and compress


@dataclass(kw_only=True, repr=False)
class ImageService:
    make_session: AsyncSessionMakerDep
    settings: SettingsDep
    store: ObjectStoreDep

    async def upload_banner(self, key: UUID, user: User, file: UploadFile) -> StorageObject:
        key_str = f"banners/{key}/"
        await self._check(key_str, user, file)
        assert file.content_type is not None

        image_bytes = await anyio.to_thread.run_sync(
            partial(
                _process_image,
                file.file,
                content_type=file.content_type,
            ),
        )

        async with self.make_session.begin() as session:
            return await self._upload(session, key_str, image_bytes)

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
        *,
        can_animate: bool = False,
        max_filesize: int = 2**20 * 10,
    ) -> StorageObject:

        # obj = StorageObject(
        #     object_key=,
        #     status=,
        #     filename=,
        #     filesize=,
        #     mime_type=,
        #     provider=await self._get_storage_provider(session),
        # )
        # session.add(obj)
        raise NotImplementedError  # TODO: upload to s3 and store in db

    async def _get_storage_provider(self, session: AsyncSession) -> StorageProvider:
        raise NotImplementedError  # TODO: upsert into db


async def get_image_service(
    make_session: AsyncSessionMakerDep,
    settings: SettingsDep,
    store: ObjectStoreDep,
) -> ImageService:
    return ImageService(make_session=make_session, settings=settings, store=store)


ImageServiceDep = Annotated[ImageService, Depends(get_image_service)]
