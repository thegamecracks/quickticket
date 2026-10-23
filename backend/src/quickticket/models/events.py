from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

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


class Venue(Base):
    __tablename__ = "venue"

    id: Mapped[pk_uuid] = mapped_column("venue_id")
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organization.organization_id", ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[current_timestamp] = mapped_column(index=True)
    display_name: Mapped[str_128]
    description: Mapped[str_4096]
    theme: Mapped[str_128]
    thumbnail_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("storage_object.storage_object_id", ondelete="SET NULL"),
    )
    banner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("storage_object.storage_object_id", ondelete="SET NULL"),
    )
    location_name: Mapped[str_128]
    location_coords: Mapped[Point | None]

    banner: Mapped[StorageObject | None] = relationship(
        foreign_keys=[banner_id],
        passive_deletes=True,
    )
    events: Mapped[list[Event]] = relationship(back_populates="venue")
    organization: Mapped[Organization] = relationship(back_populates="venues")
    thumbnail: Mapped[StorageObject | None] = relationship(
        foreign_keys=[thumbnail_id],
        passive_deletes=True,
    )


class Event(Base):
    __tablename__ = "event"

    id: Mapped[pk_uuid] = mapped_column("event_id")
    venue_id: Mapped[UUID] = mapped_column(
        ForeignKey("venue.venue_id", ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[current_timestamp] = mapped_column(index=True)
    display_name: Mapped[str_128]
    description: Mapped[str_4096]
    theme: Mapped[str_128]
    thumbnail_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("storage_object.storage_object_id", ondelete="SET NULL"),
    )
    banner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("storage_object.storage_object_id", ondelete="SET NULL"),
    )
    starts_at: Mapped[current_timestamp]  # requires user input
    ends_at: Mapped[current_timestamp]  # requires user input
    ticket_price: Mapped[Money] = mapped_column(
        default=0,
        server_default=text("""'{"amount": 0, "currency": "CAD"}'"""),
    )
    max_attendees: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    banner: Mapped[StorageObject | None] = relationship(
        foreign_keys=[banner_id],
        passive_deletes=True,
    )
    thumbnail: Mapped[StorageObject | None] = relationship(
        foreign_keys=[thumbnail_id],
        passive_deletes=True,
    )
    tickets: Mapped[list[Ticket]] = relationship(back_populates="event")
    venue: Mapped[Venue] = relationship(back_populates="events")


class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[pk_uuid] = mapped_column("ticket_id")
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("event.event_id", ondelete="CASCADE"),
        index=True,
    )
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.account_id", ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[current_timestamp] = mapped_column(index=True)
    paid_cost: Mapped[Money]

    event: Mapped[Event] = relationship(back_populates="tickets")
    user: Mapped[User] = relationship(back_populates="tickets")
