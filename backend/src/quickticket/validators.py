from typing import Annotated

from pydantic import AfterValidator, Field


def filter_string_field(value: str) -> str:
    """Strip whitespace and filter out non-printable characters."""
    value = value.strip()
    return "".join(c for c in value if c.isprintable())


DisplayNameField = Annotated[
    str, AfterValidator(filter_string_field), Field(min_length=3, max_length=128)
]
