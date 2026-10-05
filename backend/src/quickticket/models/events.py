from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.accounts import User
from quickticket.models.base import Base
from quickticket.models.money import Money
from quickticket.models.organizations import Organization
from quickticket.models.types import Point, current_timestamp, pk_uuid, str_128, str_2000, str_4096

__all__ = (
    "Event",
    "Ticket",
    "Venue",
)


class Venue(Base):
    __tablename__ = "venue"

    id: Mapped[pk_uuid] = mapped_column("venue_id")
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organization.organization_id"),
        index=True,
    )
    created_at: Mapped[current_timestamp]
    display_name: Mapped[str_128]
    description: Mapped[str_4096]
    theme: Mapped[str_128]
    thumbnail_url: Mapped[str_2000]
    banner_url: Mapped[str_2000]
    location_name: Mapped[str_128]
    location_coords: Mapped[Point | None]

    events: Mapped[list[Event]] = relationship(back_populates="venue", lazy="raise_on_sql")
    organization: Mapped[Organization] = relationship(back_populates="venues", lazy="raise_on_sql")


class Event(Base):
    __tablename__ = "event"

    id: Mapped[pk_uuid] = mapped_column("event_id")
    venue_id: Mapped[UUID] = mapped_column(
        ForeignKey("venue.venue_id"),
        index=True,
    )
    created_at: Mapped[current_timestamp]
    display_name: Mapped[str_128]
    description: Mapped[str_4096]
    theme: Mapped[str_128]
    thumbnail_url: Mapped[str_2000]
    banner_url: Mapped[str_2000]
    starts_at: Mapped[current_timestamp]  # requires user input
    ends_at: Mapped[current_timestamp]  # requires user input
    ticket_price: Mapped[Money] = mapped_column(
        default=0,
        server_default=text("""'{"amount": 0, "currency": "CAD"}'"""),
    )
    max_attendees: Mapped[int] = mapped_column(default=0, server_default=text("0"))

    tickets: Mapped[list[Ticket]] = relationship(back_populates="event", lazy="raise_on_sql")
    venue: Mapped[Venue] = relationship(back_populates="events", lazy="raise_on_sql")


class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[pk_uuid] = mapped_column("ticket_id")
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("event.event_id"),
        index=True,
    )
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.account_id", ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[current_timestamp]
    paid_cost: Mapped[Money]

    event: Mapped[Event] = relationship(back_populates="tickets", lazy="raise_on_sql")
    user: Mapped[User] = relationship(back_populates="tickets", lazy="raise_on_sql")
