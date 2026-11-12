from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid7

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.base import Base
from quickticket.models.organizations import Organization
from quickticket.models.types import (
    OrganizationID,
    Point,
    StorageObjectID,
    VenueID,
    current_timestamp,
    str_128,
    str_4096,
)

if TYPE_CHECKING:
    from quickticket.models.events import Event
    from quickticket.models.storage import StorageObject

__all__ = ("Venue",)


class Venue(Base, kw_only=True, repr=False):
    __tablename__ = "venue"

    id: Mapped[VenueID] = mapped_column("venue_id", primary_key=True, default_factory=uuid7)

    # Required
    organization_id: Mapped[OrganizationID] = mapped_column(
        ForeignKey("organization.organization_id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    display_name: Mapped[str_128]
    description: Mapped[str_4096]
    theme: Mapped[str_128]
    location_name: Mapped[str_128]

    # Optional
    created_at: Mapped[current_timestamp] = mapped_column(default=None, index=True)
    location_coords: Mapped[Point | None] = mapped_column(default=None)
    banner_id: Mapped[StorageObjectID | None] = mapped_column(
        ForeignKey("storage_object.storage_object_id", ondelete="SET NULL"),
        default=None,
    )
    thumbnail_id: Mapped[StorageObjectID | None] = mapped_column(
        ForeignKey("storage_object.storage_object_id", ondelete="SET NULL"),
        default=None,
    )

    # Relationships
    banner: Mapped[StorageObject | None] = relationship(
        default=None,
        foreign_keys=[banner_id],
        passive_deletes=True,
    )
    events: Mapped[list[Event]] = relationship(
        default_factory=list,
        back_populates="venue",
    )
    organization: Mapped[Organization] = relationship(
        default=None,
        back_populates="venues",
    )
    thumbnail: Mapped[StorageObject | None] = relationship(
        default=None,
        foreign_keys=[thumbnail_id],
        passive_deletes=True,
    )
