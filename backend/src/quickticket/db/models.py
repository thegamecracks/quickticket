from __future__ import annotations

import datetime
from typing import Annotated
from uuid import UUID

from sqlalchemy import ForeignKey, MetaData, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata_obj = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    metadata = metadata_obj


# https://docs.sqlalchemy.org/en/21/orm/declarative_tables.html#mapping-whole-column-declarations-to-python-types-with-pep-593-annotated
str_128 = Annotated[str, mapped_column(String(128))]
str_256 = Annotated[str, mapped_column(String(256))]
timestamp = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]


class User(Base):
    __tablename__ = "account"

    id: Mapped[UUID] = mapped_column("account_id", primary_key=True)
    created_at: Mapped[timestamp]
    display_name: Mapped[str_128]
    first_name: Mapped[str_128]
    last_name: Mapped[str_128]
    email: Mapped[str_256]

    addresses: Mapped[list[Address]] = relationship(back_populates="user")


class Address(Base):
    __tablename__ = "address"

    id: Mapped[UUID] = mapped_column("address_id", primary_key=True)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("account.account_id"))
    line_1: Mapped[str_128]
    line_2: Mapped[str_128]
    city: Mapped[str_128]
    province: Mapped[str_128]
    postal_code: Mapped[str_128]

    user: Mapped[User] = relationship(back_populates="addresses")
