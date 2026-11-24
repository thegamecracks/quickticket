import re
import unicodedata
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime, Field, FutureDatetime

_whitespace_pattern = re.compile(r"\s+")
_line_break_pattern = re.compile("\r\n|[\r\u2028\u2029]")


def filter_oneline_field(value: str) -> str:
    """Filter a single-line string."""
    value = filter_multiline_field(value)
    return _whitespace_pattern.sub(" ", value)


def filter_multiline_field(value: str, *, allowed_chars: str = "\n\t") -> str:
    """Filter a multi-line string, keeping only LF line breaks and tabs."""
    value = _line_break_pattern.sub("\n", value)
    value = "".join(
        c for c in value if unicodedata.category(c) not in ("Cc", "Cf", "Cs") or c in allowed_chars
    )
    return value.strip()


DisplayNameField = Annotated[
    str,
    AfterValidator(filter_oneline_field),
    Field(min_length=3, max_length=128),
]
FutureAwareDatetime = Annotated[datetime, AwareDatetime, FutureDatetime]
