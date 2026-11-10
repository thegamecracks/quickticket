from pydantic import BaseModel


class KeysetPagedResponse[E, K](BaseModel):
    """A keyset-based paginated response."""

    items: list[E]
    """The items for the current page."""
    # NOTE: maybe field specifying the relevant query parameter?
    next: K | None
    """The next key to use. If null, this is the last page."""
    total: int
    """The total number of items. May be reduced by filters."""
