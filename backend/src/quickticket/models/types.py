import re
import struct
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Annotated, Any, ClassVar, NewType, Self
from uuid import UUID

from pydantic import BaseModel, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic_core import core_schema
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
    "AddressID",
    "EventID",
    "MimeType",
    "MimeTypeSerializer",
    "NotificationID",
    "OrganizationID",
    "Point",
    "PointSerializer",
    "StorageObjectID",
    "StorageProviderID",
    "TZDateTime",
    "TicketID",
    "UserID",
    "VenueID",
    "can_cascade_delete",
    "current_timestamp",
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

AddressID = NewType("AddressID", UUID)
EventID = NewType("EventID", UUID)
NotificationID = NewType("NotificationID", UUID)
OrganizationID = NewType("OrganizationID", UUID)
StorageObjectID = NewType("StorageObjectID", UUID)
StorageProviderID = NewType("StorageProviderID", UUID)
TicketID = NewType("TicketID", UUID)
UserID = NewType("UserID", UUID)
VenueID = NewType("VenueID", UUID)

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
        if not value.tzinfo or value.tzinfo.utcoffset(value) is None:
            raise TypeError("Cannot serialize timezone-naive datetime, tzinfo= must be set")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return value
        if value.tzinfo is None:
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
        return None

    def process_result_value(self, value: bytes | None, dialect: Dialect) -> Point | None:
        if value is not None:
            lat, long = struct.unpack("<dd", value)
            return Point(lat=lat, long=long)
        return None


class MimeType(str):
    __slots__ = ()
    _pattern: ClassVar[re.Pattern] = re.compile(r"^\w+/[-+.\w]+$")

    def __new__(cls, obj: object = "") -> Self:
        ret = super().__new__(cls, obj)
        if not cls._pattern.fullmatch(ret):
            raise ValueError(f"Invalid mime type: {ret!r}")
        return ret

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.AfterValidatorFunctionSchema:
        return core_schema.with_info_after_validator_function(
            lambda value, validation_info: cls(value),
            core_schema.str_schema(),
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        schema: core_schema.CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> dict[str, Any]:
        json_schema = handler(schema)
        json_schema.update({"pattern": cls._pattern.pattern})
        return json_schema


class MimeTypeSerializer(TypeDecorator):
    """De/serialize the MimeType class to and from the database."""

    impl = String(2000)
    cache_ok = True

    def process_bind_param(self, value: MimeType | None, dialect: Dialect) -> str | None:
        if value is not None:
            return value
        return None

    def process_result_value(self, value: str | None, dialect: Dialect) -> MimeType | None:
        if value is not None:
            return MimeType(value)
        return None


# https://gist.github.com/alexa-infra/1a2488e4980e4e3c239aaf962eab06b6
# Implicitly set uuidv7() default function for UUID columns
@compiles(Uuid, "postgresql")
def compile_uuid_postgresql(element, compiler, **kw):  # noqa: ANN001, ANN003, ANN202
    expr: Column | None = kw.get("type_expression")
    if expr is None:
        return compiler.visit_UUID(element, **kw)
    if expr.server_default is not None:
        # Don't override server default if it's defined.
        return compiler.visit_UUID(element, **kw)
    if expr.nullable:
        # For nullable columns, assume a UUID default isn't required.
        return compiler.visit_UUID(element, **kw)
    if expr.foreign_keys or not expr.primary_key:
        # Don't generate UUIDs for foreign keys.
        #
        # In practice, `expr.foreign_keys` doesn't work with Alembic since ForeignKey()
        # constraints are added after the column is created.
        #
        # As a workaround, we'll only apply the default UUID for primary keys.
        return compiler.visit_UUID(element, **kw)

    expr.server_default = DefaultClause(func.uuidv7())
    return compiler.visit_UUID(element, **kw)
