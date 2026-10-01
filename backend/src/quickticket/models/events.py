from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from quickticket.models.base import Base
from quickticket.models.types import str_128, str_2000, str_4096, timestamp


class Venue(Base):
    __tablename__ = "venue"

    id: Mapped[UUID] = mapped_column("venue_id", primary_key=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organization.organization_id"))
    created_at: Mapped[timestamp]
    display_name: Mapped[str_128]
    description: Mapped[str_4096]
    theme: Mapped[str_128]
    thumbnail_url: Mapped[str_2000]
    banner_url: Mapped[str_2000]
    location_name: Mapped[str_128]
    # location_coords: insert point type here??


class Event(Base):
    __tablename__ = "event"

    id: Mapped[UUID] = mapped_column("event_id", primary_key=True)
    venue_id: Mapped[UUID] = mapped_column(ForeignKey("venue.venue_id"))
    created_at: Mapped[timestamp]
    display_name: Mapped[str_128]
    description: Mapped[str_4096]
    theme: Mapped[str_128]
    thumbnail_url: Mapped[str_2000]
    banner_url: Mapped[str_2000]
    starts_at: Mapped[timestamp]
    ends_at: Mapped[timestamp]
    ticket_price: Mapped[int]  # in cents for stripe/db cross compat
    max_attendees: Mapped[int]


class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[UUID] = mapped_column("ticket_id", primary_key=True)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("event.event_id"))
    account_id: Mapped[UUID] = mapped_column(ForeignKey("account.account_id"))
    created_at: Mapped[timestamp]
    paid_cost: Mapped[int]  # in cents for stripe/db cross compat
