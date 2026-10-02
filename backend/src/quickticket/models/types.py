import datetime
import struct
from collections.abc import Mapping
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import BaseModel
from sqlalchemy import (
    Column,
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

pk_uuid = Annotated[UUID, mapped_column(primary_key=True, default=uuid4)]

current_timestamp = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]

# https://docs.sqlalchemy.org/en/21/orm/cascades.html
can_cascade_delete: Mapping[str, Any] = {
    "cascade": "save-update, delete, delete-orphan, merge, expunge",
    "passive_deletes": True,
}


class Point(BaseModel):
    """A (latitiude, longitude) coordinate pair."""

    lat: float
    long: float


class PointSerializer(TypeDecorator):
    """De/serialize the Point class to and from the database."""

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value: Point | None, dialect: Dialect):
        if value is not None:
            return struct.pack("<dd", value.lat, value.long)

    def process_result_value(self, value: bytes | None, dialect: Dialect):
        if value is not None:
            lat, long = struct.unpack("<dd", value)
            return Point(lat=lat, long=long)


# https://gist.github.com/alexa-infra/1a2488e4980e4e3c239aaf962eab06b6
# Set uuidv4() default function for non-foreign key UUID columns
@compiles(Uuid, "postgresql")
def compile_uuid_postgresql(element, compiler, **kw):
    expr: Column | None = kw.get("type_expression")
    if expr is not None and not expr.server_default and not expr.foreign_keys:
        expr.server_default = DefaultClause(func.uuidv4())
    return compiler.visit_UUID(element, **kw)
