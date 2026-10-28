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
    from quickticket.models.storage import StorageObject

__all__ = (
    "Address",
    "Notification",
    "OpenIDAccount",
    "User",
)


class User(Base, kw_only=True, repr=False):
    __tablename__ = "account"

    id: Mapped[pk_uuid] = mapped_column("account_id", default=None)

    # Required
    display_name: Mapped[str_128]
    first_name: Mapped[str_128]
    last_name: Mapped[str_128]
    email: Mapped[str_256] = mapped_column(unique=True)

    # Optional
    created_at: Mapped[current_timestamp] = mapped_column(default=None, index=True)

    # Relationships
    addresses: Mapped[list[Address]] = relationship(
        default_factory=list,
        back_populates="user",
        **can_cascade_delete,
    )
    notifications: Mapped[list[Notification]] = relationship(
        default_factory=list,
        back_populates="user",
        **can_cascade_delete,
    )
    openid_accounts: Mapped[list[OpenIDAccount]] = relationship(
        default_factory=list,
        back_populates="user",
        **can_cascade_delete,
    )
    organizations: Mapped[list[Organization]] = relationship(
        default_factory=list,
        # back_populates="users",
        secondary="organization_member",
        viewonly=True,
    )
    organization_members: Mapped[list[OrganizationMember]] = relationship(
        default_factory=list,
        back_populates="user",
    )
    storage_objects: Mapped[list[StorageObject]] = relationship(
        default_factory=list,
        passive_deletes=True,
    )
    tickets: Mapped[list[Ticket]] = relationship(
        default_factory=list,
        back_populates="user",
        **can_cascade_delete,
    )


class OpenIDAccount(Base, kw_only=True, repr=False):
    __tablename__ = "account_openid"

    # Required
    issuer: Mapped[str] = mapped_column(String(2000), primary_key=True)
    """The OpenID provider that issued this account."""
    sub: Mapped[str] = mapped_column(String(2000), primary_key=True)
    """The provider's unique identifier for this account."""
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.account_id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    """The account that linked this provider's identity."""

    # Optional
    id_token: Mapped[str | None] = mapped_column(default=None)
    """The last known ID token received from this provider.

    This is used to perform RP-initiated logouts.
    https://openid.net/specs/openid-connect-rpinitiated-1_0.html

    """

    # Relationships
    user: Mapped[User] = relationship(
        default=None,
        back_populates="openid_accounts",
    )


class Address(Base, kw_only=True, repr=False):
    __tablename__ = "address"

    id: Mapped[pk_uuid] = mapped_column("address_id", default=None)

    # Required
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.account_id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    line_1: Mapped[str_128]
    line_2: Mapped[str_128]
    city: Mapped[str_128]
    province: Mapped[str_128]
    postal_code: Mapped[str_128]

    # Relationships
    user: Mapped[User] = relationship(
        default=None,
        back_populates="addresses",
    )


class Notification(Base, kw_only=True, repr=False):
    __tablename__ = "notification"

    id: Mapped[pk_uuid] = mapped_column("notification_id", default=None)

    # Required
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.account_id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    expires_at: Mapped[datetime]
    is_read: Mapped[bool]
    content_short: Mapped[str_1024]
    content_full: Mapped[str_4096]

    # Optional
    created_at: Mapped[current_timestamp] = mapped_column(default=None)
    email_at: Mapped[datetime | None] = mapped_column(default=None)

    # Relationships
    user: Mapped[User] = relationship(
        default=None,
        back_populates="notifications",
    )
