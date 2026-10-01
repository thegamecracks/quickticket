import datetime
from typing import Annotated

from sqlalchemy import String, func, Integer, Text
from sqlalchemy.orm import mapped_column

# https://docs.sqlalchemy.org/en/21/orm/declarative_tables.html#mapping-whole-column-declarations-to-python-types-with-pep-593-annotated
str_128 = Annotated[str, mapped_column(String(128))]
str_256 = Annotated[str, mapped_column(String(256))]
str_1024 = Annotated[str, mapped_column(String(1024))]
str_2000 = Annotated[str, mapped_column(String(2000))]
str_4096 = Annotated[str, mapped_column(String(4096))]

timestamp = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]