from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.base import Base
from quickticket.models.types import str_128, str_256, timestamp


class User(Base):
    __tablename__ = "account"

    id: Mapped[UUID] = mapped_column("account_id", primary_key=True, default=uuid4)
    created_at: Mapped[timestamp]
    display_name: Mapped[str_128]
    first_name: Mapped[str_128]
    last_name: Mapped[str_128]
    email: Mapped[str_256] = mapped_column(unique=True)

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
