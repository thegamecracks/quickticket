from datetime import datetime
from typing import Annotated, Self

from pydantic import AwareDatetime, BaseModel, Field, model_validator

DateTimeSortKey = Annotated[datetime, AwareDatetime]
"""A timezone-aware datetime used as a keyset pagination sort key."""


class DateTimeFilterParams(BaseModel):
    """Filter parameters based on some time field."""

    after: Annotated[datetime, AwareDatetime] | None = Field(
        description="Return items after the given datetime, exclusive.",
        default=None,
    )

    before: Annotated[datetime, AwareDatetime] | None = Field(
        description="Return items before the given datetime, exclusive.",
        default=None,
    )

    @model_validator(mode="after")
    def check_after_before(self) -> Self:
        if self.after is not None and self.before is not None and self.after >= self.before:
            raise ValueError("after must be before before")
        return self


class KeysetPageParams[K](BaseModel):
    """Parameters for keyset pagination."""

    next: K | None = Field(
        description="Get the next page by key.",
        default=None,
    )

    limit: int = Field(
        description="Limit the number of items returned.",
        default=10,
        gt=0,
        le=10,
    )

    # sort: Annotated[SortKey | None, AfterValidator(parse_sort_key)] = Field(
    #     description="Sort by a given attribute in ascending (+) or descending (-) order.",
    #     default=None,
    # )


class KeysetPagedResponse[E, K](BaseModel):
    """A keyset-based paginated response."""

    items: list[E]
    """The items for the current page."""
    # NOTE: maybe field specifying the relevant query parameter?
    next: K | None
    """The next key to use. If null, this is the last page."""
    total: int
    """The total number of (potentially filtered) items."""
