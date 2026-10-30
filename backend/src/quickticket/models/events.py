from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.accounts import User
from quickticket.models.base import Base
from quickticket.models.money import Money
from quickticket.models.organizations import Organization
from quickticket.models.types import Point, current_timestamp, pk_uuid, str_128, str_4096

if TYPE_CHECKING:
    from quickticket.models.storage import StorageObject

__all__ = (
    "Event",
    "Ticket",
    "Venue",
)


class Venue(Base, kw_only=True, repr=False):
    __tablename__ = "venue"

    id: Mapped[pk_uuid] = mapped_column("venue_id", default_factory=uuid4)

    # Required
    organization_id: Mapped[UUID] = mapped_column(
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
    banner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("storage_object.storage_object_id", ondelete="SET NULL"),
        default=None,
    )
    thumbnail_id: Mapped[UUID | None] = mapped_column(
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


class Event(Base, kw_only=True, repr=False):
    __tablename__ = "event"

    id: Mapped[pk_uuid] = mapped_column("event_id", default_factory=uuid4)

    # Required
    venue_id: Mapped[UUID] = mapped_column(
        ForeignKey("venue.venue_id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    display_name: Mapped[str_128]
    description: Mapped[str_4096]
    theme: Mapped[str_128]
    starts_at: Mapped[current_timestamp]  # requires user input
    ends_at: Mapped[current_timestamp]  # requires user input

    # Optional
    created_at: Mapped[current_timestamp] = mapped_column(default=None, index=True)
    max_attendees: Mapped[int] = mapped_column(default=0, server_default=text("0"))
    ticket_price: Mapped[Money] = mapped_column(
        default=Money(amount=0, currency="CAD"),
        server_default=text("""'{"amount": 0, "currency": "CAD"}'"""),
    )
    banner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("storage_object.storage_object_id", ondelete="SET NULL"),
        default=None,
    )
    thumbnail_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("storage_object.storage_object_id", ondelete="SET NULL"),
        default=None,
    )

    # Relationships
    banner: Mapped[StorageObject | None] = relationship(
        default=None,
        foreign_keys=[banner_id],
        passive_deletes=True,
    )
    thumbnail: Mapped[StorageObject | None] = relationship(
        default=None,
        foreign_keys=[thumbnail_id],
        passive_deletes=True,
    )
    tickets: Mapped[list[Ticket]] = relationship(
        default_factory=list,
        back_populates="event",
    )
    venue: Mapped[Venue] = relationship(
        default=None,
        back_populates="events",
    )


class Ticket(Base, kw_only=True, repr=False):
    __tablename__ = "ticket"

    id: Mapped[pk_uuid] = mapped_column("ticket_id", default_factory=uuid4)

    # Required
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("event.event_id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.account_id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    paid_cost: Mapped[Money]

    # Optional
    created_at: Mapped[current_timestamp] = mapped_column(default=None, index=True)

    # Relationships
    event: Mapped[Event] = relationship(
        default=None,
        back_populates="tickets",
    )
    user: Mapped[User] = relationship(
        default=None,
        back_populates="tickets",
    )
