from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid7

from sqlalchemy import CheckConstraint, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.base import Base
from quickticket.models.money import Money
from quickticket.models.tickets import Ticket
from quickticket.models.types import (
    EventID,
    StorageObjectID,
    VenueID,
    current_timestamp,
    str_128,
    str_4096,
)
from quickticket.models.venues import Venue

if TYPE_CHECKING:
    from quickticket.models.storage import StorageObject

__all__ = ("Event",)


class Event(Base, kw_only=True, repr=False):
    __tablename__ = "event"

    id: Mapped[EventID] = mapped_column("event_id", primary_key=True, default_factory=uuid7)

    # Required
    venue_id: Mapped[VenueID] = mapped_column(
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
    max_attendees: Mapped[int] = mapped_column(
        CheckConstraint("max_attendees >= 0", "max_attendees_positive"),
        default=0,
        server_default=text("0"),
    )
    ticket_price: Mapped[Money] = mapped_column(
        default=Money(amount=0, currency="CAD"),
        server_default=text("""'{"amount": 0, "currency": "CAD"}'"""),
    )
    banner_id: Mapped[StorageObjectID | None] = mapped_column(
        ForeignKey("storage_object.storage_object_id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    thumbnail_id: Mapped[StorageObjectID | None] = mapped_column(
        ForeignKey("storage_object.storage_object_id", ondelete="SET NULL"),
        default=None,
        index=True,
    )

    # Relationships
    banner: Mapped[StorageObject | None] = relationship(
        default=None,
        foreign_keys=[banner_id],
    )
    thumbnail: Mapped[StorageObject | None] = relationship(
        default=None,
        foreign_keys=[thumbnail_id],
    )
    tickets: Mapped[list[Ticket]] = relationship(
        default_factory=list,
        back_populates="event",
    )
    venue: Mapped[Venue] = relationship(
        default=None,
        back_populates="events",
    )
