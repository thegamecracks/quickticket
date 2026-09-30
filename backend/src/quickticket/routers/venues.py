import logging
from uuid import UUID

from fastapi import APIRouter

router = APIRouter(tags=["Venues"])
log = logging.getLogger(__name__)


@router.get("")
async def get_venues() -> None:
    """Get a list of venues."""
    # TODO: sort by location proximity in latitude/longitude
    # TODO: support pagination
    # TODO: maybe support FTS search?


@router.get("/{venue_id}")
async def get_venue(venue_id: UUID) -> None:
    """Get a venue by ID."""
    # TODO: load events
    # TODO: load organization
    # TODO: load user's tickets for venue if logged in


@router.post("")
async def create_venue() -> None:
    """Create a new venue in an organization."""
    # TODO: check authorization by organization
    # TODO: cap venues to five per organization?
    # TODO: allow venue drafts?


@router.patch("/{venue_id}")
async def edit_venue(venue_id: UUID) -> None:
    """Edit a venue's details."""
    # TODO: check authorization by organization
    # TODO: allow venue drafts?


@router.delete("/{venue_id}")
async def delete_venue(venue_id: UUID) -> None:
    """Delete a venue."""
    # TODO: check authorization by organization
    # TODO: block venue deletion if any tickets are issued
