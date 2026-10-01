from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.base import Base
from quickticket.models.types import str_128, str_256, str_1024, str_4096, timestamp


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
