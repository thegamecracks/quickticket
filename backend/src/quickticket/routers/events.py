import logging
from uuid import UUID

from fastapi import APIRouter

router = APIRouter()
log = logging.getLogger(__name__)


@router.get("/")
async def get_events() -> None:
    """Get a list of events."""
    # TODO: sort by newest events, most tickets?
    # TODO: support pagination
    # TODO: maybe support FTS search?


@router.get("/{event_id}")
async def get_event(event_id: UUID) -> None:
    """Get an event by ID."""
    # TODO: load venue
    # TODO: load organization
    # TODO: load user's tickets for event if logged in


@router.post("/")
async def create_event() -> None:
    """Create a new event for a venue."""
    # TODO: check authorization by organization
    # TODO: schedule notifications
    # TODO: allow event drafts?


@router.patch("/{event_id}")
async def edit_event(event_id: UUID) -> None:
    """Edit an event's details."""
    # TODO: check authorization by organization
    # TODO: schedule notifications
    # TODO: allow event drafts?


@router.delete("/{event_id}")
async def delete_event(event_id: UUID) -> None:
    """Delete an event."""
    # TODO: check authorization by organization
    # TODO: block event deletion if any tickets are issued
