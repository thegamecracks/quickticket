from collections.abc import Mapping
from typing import ClassVar

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from quickticket.models.money import Money, MoneySerializer

__all__ = ("Base",)

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata_obj = MetaData(naming_convention=convention)


class Base(AsyncAttrs, DeclarativeBase):
    metadata = metadata_obj
    # https://docs.sqlalchemy.org/en/21/core/custom_types.html#linking-python-uuid-uuid-to-the-custom-type-for-orm-mappings
    type_annotation_map: ClassVar[Mapping[type, object]] = {
        Money: MoneySerializer,
    }
