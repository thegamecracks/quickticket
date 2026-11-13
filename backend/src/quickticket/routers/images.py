import logging
from collections.abc import Callable, Sequence
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import AwareDatetime, BaseModel
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import ORMOption

from quickticket.dependencies.auth import RequiredUserDep
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.dependencies.images import BannerEntity, ImageServiceDep
from quickticket.dependencies.models import get_organization_controller
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
    filesize: str
    mime_type: MimeType
    created_at: AwareDatetime


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
        name=f"edit_{entity_name}_banner",
        response_model=ImageRead,
    )
    async def edit_banner(
        user: RequiredUserDep,
        session: AsyncSessionDep,
        images: ImageServiceDep,
        entity_id: UUID,
        file: UploadFile,
    ) -> StorageObject:
        """Edit this entity's banner."""
        entity = await session.get(entity_cls, entity_id, options=options)
        if entity is None:
            raise ORMEntityNotFound(entity_cls, entity_id)

        controller = await get_organization_controller(session, user, get_organization_id(entity))
        controller.assert_permissions(OrganizationMemberPermissions.ADMINISTRATOR)

        return await images.upload_banner(entity, file, user=user)

    @router.delete(
        "/{entity_id}/banner",
        name=f"delete_{entity_name}_banner",
        status_code=204,
    )
    async def delete_banner(
        user: RequiredUserDep,
        session: AsyncSessionDep,
        entity_id: UUID,
    ) -> None:
        """Delete this entity's banner."""
        entity = await session.get(entity_cls, entity_id, options=[*options, load_banner])
        if entity is None:
            raise ORMEntityNotFound(entity_cls, entity_id)

        controller = await get_organization_controller(session, user, get_organization_id(entity))
        controller.assert_permissions(OrganizationMemberPermissions.ADMINISTRATOR)

        if entity.banner is None:
            raise HTTPException(404, "Image not set")

        # TODO: schedule image for deletion
        entity.banner = None

    return router
