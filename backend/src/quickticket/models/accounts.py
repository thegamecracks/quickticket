from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.base import Base
from quickticket.models.types import (
    can_cascade_delete,
    current_timestamp,
    pk_uuid,
    str_128,
    str_256,
    str_1024,
    str_4096,
)

if TYPE_CHECKING:
    from quickticket.models.events import Ticket
    from quickticket.models.organizations import Organization, OrganizationMember

__all__ = (
    "Address",
    "Notification",
    "OpenIDAccount",
    "User",
)


class User(Base):
    __tablename__ = "account"

    id: Mapped[pk_uuid] = mapped_column("account_id")
    created_at: Mapped[current_timestamp]

    # Fields derived from provider
    display_name: Mapped[str_128]
    first_name: Mapped[str_128]
    last_name: Mapped[str_128]
    email: Mapped[str_256] = mapped_column(unique=True)

    addresses: Mapped[list[Address]] = relationship(
        back_populates="user",
        lazy="raise_on_sql",
        **can_cascade_delete,
    )
    notifications: Mapped[list[Notification]] = relationship(
        back_populates="user",
        lazy="raise_on_sql",
        **can_cascade_delete,
    )
    openid_accounts: Mapped[list[OpenIDAccount]] = relationship(
        back_populates="user",
        lazy="raise_on_sql",
        **can_cascade_delete,
    )
    organizations: Mapped[list[Organization]] = relationship(
        # back_populates="users",
        lazy="raise_on_sql",
        secondary="organization_member",
        viewonly=True,
    )
    organization_members: Mapped[list[OrganizationMember]] = relationship(
        back_populates="user",
        lazy="raise_on_sql",
    )
    tickets: Mapped[list[Ticket]] = relationship(
        back_populates="user",
        lazy="raise_on_sql",
        **can_cascade_delete,
    )


class OpenIDAccount(Base):
    __tablename__ = "account_openid"

    issuer: Mapped[str] = mapped_column(String(2000), primary_key=True)
    """The OpenID provider that issued this account."""
    sub: Mapped[str] = mapped_column(String(2000), primary_key=True)
    """The provider's unique identifier for this account."""
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.account_id", ondelete="CASCADE"),
        index=True,
    )
    """The account that linked this provider's identity."""
    id_token: Mapped[str | None]
    """The last known ID token received from this provider.

    This is used to perform RP-initiated logouts.
    https://openid.net/specs/openid-connect-rpinitiated-1_0.html

    """

    user: Mapped[User] = relationship(back_populates="openid_accounts", lazy="raise_on_sql")


class Address(Base):
    __tablename__ = "address"

    id: Mapped[pk_uuid] = mapped_column("address_id")
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.account_id", ondelete="CASCADE"),
        index=True,
    )
    line_1: Mapped[str_128]
    line_2: Mapped[str_128]
    city: Mapped[str_128]
    province: Mapped[str_128]
    postal_code: Mapped[str_128]

    user: Mapped[User] = relationship(back_populates="addresses", lazy="raise_on_sql")


class Notification(Base):
    __tablename__ = "notification"

    id: Mapped[pk_uuid] = mapped_column("notification_id")
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.account_id", ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[current_timestamp]
    expires_at: Mapped[datetime]
    email_at: Mapped[datetime | None]
    is_read: Mapped[bool]
    content_short: Mapped[str_1024]
    content_full: Mapped[str_4096]

    user: Mapped[User] = relationship(back_populates="notifications", lazy="raise_on_sql")
