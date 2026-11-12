import struct
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID, uuid7

from pydantic import BaseModel
from sqlalchemy import (
    Column,
    DateTime,
    DefaultClause,
    Dialect,
    LargeBinary,
    String,
    TypeDecorator,
    Uuid,
    func,
    text,
)
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import mapped_column

__all__ = (
    "Point",
    "PointSerializer",
    "TZDateTime",
    "can_cascade_delete",
    "current_timestamp",
    "pk_uuid",
    "str_128",
    "str_256",
    "str_1024",
    "str_2000",
    "str_4096",
)

# https://docs.sqlalchemy.org/en/21/orm/declarative_tables.html#mapping-whole-column-declarations-to-python-types-with-pep-593-annotated
str_128 = Annotated[str, mapped_column(String(128), server_default=text("''"))]
str_256 = Annotated[str, mapped_column(String(256), server_default=text("''"))]
str_1024 = Annotated[str, mapped_column(String(1024), server_default=text("''"))]
str_2000 = Annotated[str, mapped_column(String(2000), server_default=text("''"))]
str_4096 = Annotated[str, mapped_column(String(4096), server_default=text("''"))]

pk_uuid = Annotated[UUID, mapped_column(primary_key=True, default=uuid7)]

current_timestamp = Annotated[
    datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]

# https://docs.sqlalchemy.org/en/21/orm/cascades.html
can_cascade_delete: Mapping[str, Any] = {
    "cascade": "save-update, delete, delete-orphan, merge, expunge",
    "passive_deletes": True,
}


# https://docs.sqlalchemy.org/en/21/core/custom_types.html#store-timezone-aware-timestamps-as-timezone-naive-utc
class TZDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return value
        elif not value.tzinfo or value.tzinfo.utcoffset(value) is None:
            raise TypeError("Cannot serialize timezone-naive datetime, tzinfo= must be set")
        else:
            return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return value
        elif value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


class Point(BaseModel):
    """A (latitiude, longitude) coordinate pair."""

    lat: float
    long: float


class PointSerializer(TypeDecorator):
    """De/serialize the Point class to and from the database."""

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value: Point | None, dialect: Dialect) -> bytes | None:
        if value is not None:
            return struct.pack("<dd", value.lat, value.long)

    def process_result_value(self, value: bytes | None, dialect: Dialect) -> Point | None:
        if value is not None:
            lat, long = struct.unpack("<dd", value)
            return Point(lat=lat, long=long)


# https://gist.github.com/alexa-infra/1a2488e4980e4e3c239aaf962eab06b6
# Implicitly set uuidv7() default function for UUID columns
@compiles(Uuid, "postgresql")
def compile_uuid_postgresql(element, compiler, **kw):  # noqa: ANN001, ANN003, ANN202
    expr: Column | None = kw.get("type_expression")
    if expr is None:
        return compiler.visit_UUID(element, **kw)
    elif expr.server_default is not None:
        # Don't override server default if it's defined.
        return compiler.visit_UUID(element, **kw)
    elif expr.nullable:
        # For nullable columns, assume a UUID default isn't required.
        return compiler.visit_UUID(element, **kw)
    elif expr.foreign_keys or not expr.primary_key:
        # Don't generate UUIDs for foreign keys.
        #
        # In practice, `expr.foreign_keys` doesn't work with Alembic since ForeignKey()
        # constraints are added after the column is created.
        #
        # As a workaround, we'll only apply the default UUID for primary keys.
        return compiler.visit_UUID(element, **kw)

    expr.server_default = DefaultClause(func.uuidv7())
    return compiler.visit_UUID(element, **kw)
