from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.base import Base
from quickticket.models.types import str_128, str_256, str_1024, str_2000, str_4096, timestamp

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
    ticket_price: Mapped[int] # in cents for stripe/db cross compat
    max_attendees: Mapped[int]

class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[UUID] = mapped_column("ticket_id", primary_key=True)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("event.event_id"))
    account_id: Mapped[UUID] = mapped_column(ForeignKey("account.account_id"))
    created_at: Mapped[timestamp]
    paid_cost: Mapped[int] # in cents for stripe/db cross compat

class Organization(Base):
    __tablename__ = "organization"

    id: Mapped[UUID] = mapped_column("organization_id", primary_key=True)
    created_at: Mapped[timestamp]
    display_name: Mapped[str_128]

class OrganizationMember(Base):
    __tablename__ = "organization_member"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organization.organization_id"), primary_key=True)
    acccount_id: Mapped[UUID] = mapped_column(ForeignKey("account.account_id"), primary_key=True)
    created_at: Mapped[timestamp]
    permissions: Mapped[int] # ! todo: make sure this is 128 bit

class User(Base):
    __tablename__ = "account"

    id: Mapped[UUID] = mapped_column("account_id", primary_key=True, default=uuid4)
    created_at: Mapped[timestamp]

    # Fields derived from provider
    display_name: Mapped[str_128]
    first_name: Mapped[str_128]
    last_name: Mapped[str_128]
    email: Mapped[str_256] = mapped_column(unique=True)
    openid_sub: Mapped[str | None] = mapped_column(unique=True)
    """The provider's unique identifier for this account.

    When a user logs in via OpenID Connect, the ``sub`` claim maps to this column.
    This will impose lock-in between providers due to complications in migrating
    between provider account IDs.

    """

    addresses: Mapped[list[Address]] = relationship(back_populates="user")

class Address(Base):
    __tablename__ = "address"

    id: Mapped[UUID] = mapped_column("address_id", primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("account.account_id"))
    line_1: Mapped[str_128]
    line_2: Mapped[str_128]
    city: Mapped[str_128]
    province: Mapped[str_128]
    postal_code: Mapped[str_128]

    user: Mapped[User] = relationship(back_populates="addresses")

class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[UUID] = mapped_column("notification_id", primary_key=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("account.account_id"))
    created_at: Mapped[timestamp]
    expires_at: Mapped[timestamp]
    email_at: Mapped[timestamp]
    is_read: Mapped[bool]
    content_short: Mapped[str_1024]
    content_full: Mapped[str_4096]