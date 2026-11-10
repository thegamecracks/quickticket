from datetime import datetime

from pydantic import BaseModel, Field


class BeforePageParams(BaseModel):
    """Pagination parameters for ?before= sorting key."""

    before: datetime | None = Field(
        description="Return items before the given datetime, exclusive.",
        default=None,
    )
    limit: int = Field(
        description="Limit the number of items returned.",
        default=10,
        gt=0,
        le=10,
    )


class KeysetPagedResponse[E, K](BaseModel):
    """A keyset-based paginated response."""

    items: list[E]
    """The items for the current page."""
    # NOTE: maybe field specifying the relevant query parameter?
    next: K | None
    """The next key to use. If null, this is the last page."""
    total: int
    """The total number of (potentially filtered) items."""
