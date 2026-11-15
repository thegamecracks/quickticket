import logging
from collections.abc import Callable, Sequence
from typing import Protocol
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import AwareDatetime, BaseModel
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import ORMOption

from quickticket.dependencies.auth import RequiredUserDep
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.dependencies.images import ImageServiceDep
from quickticket.dependencies.models import get_organization_controller
from quickticket.dependencies.store import ObjectStoreDep
from quickticket.errors import ORMEntityNotFound
from quickticket.models import (
    Base,
    MimeType,
    OrganizationID,
    OrganizationMemberPermissions,
    StorageObject,
)

log = logging.getLogger(__name__)


class ImageRead(BaseModel):
    id: UUID
    filename: str
    filesize: int
    mime_type: MimeType
    created_at: AwareDatetime


class BannerEntity(Protocol):
    banner: StorageObject | None

    @property
    def id(self) -> UUID | None: ...


class ThumbnailEntity(Protocol):
    thumbnail: StorageObject | None

    @property
    def id(self) -> UUID | None: ...


def create_banner_routes[T: BannerEntity](
    entity_cls: type[T],
    *,
    get_organization_id: Callable[[T], OrganizationID],
    options: Sequence[ORMOption],
) -> APIRouter:
    """Create a router for modifying an entity's banner.

    :param entity_cls:
        The entity class to add routes for.
        Must inherit from :class:`Base`.
    :param get_organization_id:
        The function for retrieving the entity's associated organization.
    :param options:
        A list of ORM options passed to `session.get()`.
        Useful when the entity's parent organization needs to be retrieved
        from a relationship.
    """
    assert issubclass(entity_cls, Base)  # intersection type in ty

    router = APIRouter()
    load_banner = selectinload(entity_cls.banner)  # ty: ignore[invalid-argument-type]
    entity_name = entity_cls.__tablename__

    @router.get(
        "/{entity_id}/banner",
        name=f"get_{entity_name}_banner",
        response_model=None,
        responses={
            307: {"description": "Redirecting to image source."},
            404: {"description": "The image does not exist."},
        },
        status_code=404,
    )
    async def get_banner(
        session: AsyncSessionDep,
        images: ImageServiceDep,
        entity_id: UUID,
    ) -> RedirectResponse | None:
        """Get this entity's banner."""
        entity = await session.get(entity_cls, entity_id, options=[*options, load_banner])
        if entity is None:
            raise ORMEntityNotFound(entity_cls, entity_id)
        if entity.banner is None:
            return None
        return RedirectResponse(await images.get_url(entity.banner), 307)

    @router.put(
        "/{entity_id}/banner",
        name=f"set_{entity_name}_banner",
        response_model=ImageRead,
    )
    async def set_banner(
        user: RequiredUserDep,
        session: AsyncSessionDep,
        images: ImageServiceDep,
        entity_id: UUID,
        file: UploadFile,
    ) -> StorageObject:
        """Set this entity's banner."""
        entity = await session.get(entity_cls, entity_id, options=options)
        if entity is None:
            raise ORMEntityNotFound(entity_cls, entity_id)

        controller = await get_organization_controller(session, user, get_organization_id(entity))
        controller.assert_permissions(OrganizationMemberPermissions.ADMINISTRATOR)

        entity.banner = await images.upload_banner(entity, file, user=user)
        return entity.banner

    @router.delete(
        "/{entity_id}/banner",
        name=f"delete_{entity_name}_banner",
        status_code=204,
    )
    async def delete_banner(
        user: RequiredUserDep,
        session: AsyncSessionDep,
        store: ObjectStoreDep,
        entity_id: UUID,
    ) -> None:
        """Delete this entity's banner."""
        entity = await session.get(entity_cls, entity_id, options=[*options, load_banner])
        if entity is None:
            raise ORMEntityNotFound(entity_cls, entity_id)

        controller = await get_organization_controller(session, user, get_organization_id(entity))
        controller.assert_permissions(OrganizationMemberPermissions.ADMINISTRATOR)

        banner = entity.banner
        if banner is None:
            raise HTTPException(404, "Image not set")

        await store.delete_async(banner.object_key)
        await session.delete(banner)

    return router


def create_thumbnail_routes[T: ThumbnailEntity](
    entity_cls: type[T],
    *,
    get_organization_id: Callable[[T], OrganizationID],
    options: Sequence[ORMOption],
) -> APIRouter:
    """Create a router for modifying an entity's thumbnail.

    :param entity_cls:
        The entity class to add routes for.
        Must inherit from :class:`Base`.
    :param get_organization_id:
        The function for retrieving the entity's associated organization.
    :param options:
        A list of ORM options passed to `session.get()`.
        Useful when the entity's parent organization needs to be retrieved
        from a relationship.
    """
    assert issubclass(entity_cls, Base)  # intersection type in ty

    router = APIRouter()
    load_thumbnail = selectinload(entity_cls.thumbnail)  # ty: ignore[invalid-argument-type]
    entity_name = entity_cls.__tablename__

    @router.get(
        "/{entity_id}/thumbnail",
        name=f"get_{entity_name}_thumbnail",
        response_model=None,
        responses={
            307: {"description": "Redirecting to image source."},
            404: {"description": "The image does not exist."},
        },
        status_code=404,
    )
    async def get_thumbnail(
        session: AsyncSessionDep,
        images: ImageServiceDep,
        entity_id: UUID,
    ) -> RedirectResponse | None:
        """Get this entity's thumbnail."""
        entity = await session.get(entity_cls, entity_id, options=[*options, load_thumbnail])
        if entity is None:
            raise ORMEntityNotFound(entity_cls, entity_id)
        if entity.thumbnail is None:
            return None
        return RedirectResponse(await images.get_url(entity.thumbnail), 307)

    @router.put(
        "/{entity_id}/thumbnail",
        name=f"set_{entity_name}_thumbnail",
        response_model=ImageRead,
    )
    async def set_thumbnail(
        user: RequiredUserDep,
        session: AsyncSessionDep,
        images: ImageServiceDep,
        entity_id: UUID,
        file: UploadFile,
    ) -> StorageObject:
        """Set this entity's thumbnail."""
        entity = await session.get(entity_cls, entity_id, options=options)
        if entity is None:
            raise ORMEntityNotFound(entity_cls, entity_id)

        controller = await get_organization_controller(session, user, get_organization_id(entity))
        controller.assert_permissions(OrganizationMemberPermissions.ADMINISTRATOR)

        entity.thumbnail = await images.upload_thumbnail(entity, file, user=user)
        return entity.thumbnail

    @router.delete(
        "/{entity_id}/thumbnail",
        name=f"delete_{entity_name}_thumbnail",
        status_code=204,
    )
    async def delete_thumbnail(
        user: RequiredUserDep,
        session: AsyncSessionDep,
        store: ObjectStoreDep,
        entity_id: UUID,
    ) -> None:
        """Delete this entity's thumbnail."""
        entity = await session.get(entity_cls, entity_id, options=[*options, load_thumbnail])
        if entity is None:
            raise ORMEntityNotFound(entity_cls, entity_id)

        controller = await get_organization_controller(session, user, get_organization_id(entity))
        controller.assert_permissions(OrganizationMemberPermissions.ADMINISTRATOR)

        thumbnail = entity.thumbnail
        if thumbnail is None:
            raise HTTPException(404, "Image not set")

        await store.delete_async(thumbnail.object_key)
        await session.delete(thumbnail)

    return router
