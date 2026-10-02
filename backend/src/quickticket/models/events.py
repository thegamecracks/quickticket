from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.accounts import User
from quickticket.models.base import Base
from quickticket.models.money import Money
from quickticket.models.organizations import Organization
from quickticket.models.types import Point, str_128, str_2000, str_4096, timestamp

__all__ = (
    "Event",
    "Ticket",
    "Venue",
)


class Venue(Base):
    __tablename__ = "venue"

    id: Mapped[UUID] = mapped_column("venue_id", primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organization.organization_id"),
        index=True,
    )
    created_at: Mapped[timestamp]
    display_name: Mapped[str_128]
    description: Mapped[str_4096]
    theme: Mapped[str_128]
    thumbnail_url: Mapped[str_2000]
    banner_url: Mapped[str_2000]
    location_name: Mapped[str_128]
    location_coords: Mapped[Point | None]

    event: Mapped[list[Event]] = relationship(back_populates="venue")
    organization: Mapped[Organization] = relationship(back_populates="venues")


class Event(Base):
    __tablename__ = "event"

    id: Mapped[UUID] = mapped_column("event_id", primary_key=True)
    venue_id: Mapped[UUID] = mapped_column(
        ForeignKey("venue.venue_id"),
        index=True,
    )
    created_at: Mapped[timestamp]
    display_name: Mapped[str_128]
    description: Mapped[str_4096]
    theme: Mapped[str_128]
    thumbnail_url: Mapped[str_2000]
    banner_url: Mapped[str_2000]
    starts_at: Mapped[timestamp]
    ends_at: Mapped[timestamp]
    ticket_price: Mapped[Money]
    max_attendees: Mapped[int]

    tickets: Mapped[list[Ticket]] = relationship(back_populates="event")
    venue: Mapped[Venue] = relationship(back_populates="events")


class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[UUID] = mapped_column("ticket_id", primary_key=True)
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("event.event_id"),
        index=True,
    )
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.account_id", ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[timestamp]
    paid_cost: Mapped[Money]

    event: Mapped[Event] = relationship(back_populates="tickets")
    user: Mapped[User] = relationship(back_populates="tickets")
