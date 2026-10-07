import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import false, select
from sqlalchemy.orm import selectinload

from quickticket.dependencies.auth import OptionalUserDep
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.models import Event, Point, Ticket, Venue

router = APIRouter(tags=["Venues"])
log = logging.getLogger(__name__)


class VenueReadTicket(BaseModel):
    id: UUID


class VenueReadEvent(BaseModel):
    id: UUID
    tickets: list[VenueReadTicket]


class VenueReadOrganization(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str


class VenueRead(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str
    description: str
    theme: str
    thumbnail_url: str
    banner_url: str
    location_name: str
    location_coords: Point | None

    events: list[VenueReadEvent]
    organization: VenueReadOrganization


class VenuesRead(BaseModel):
    venues: list[VenueRead]


@router.get("", response_model=VenuesRead)
async def get_venues(user: OptionalUserDep, session: AsyncSessionDep) -> Any:
    """Get a list of venues."""
    # TODO: sort by location proximity in latitude/longitude
    # TODO: support pagination
    # TODO: maybe support FTS search?
    venues = await session.scalars(
        select(Venue)
        # .join(Event, Venue.events)
        # .join(Ticket, Event.tickets)
        # .join(Organization, Venue.organization)
        .order_by(Venue.created_at.desc())
        .options(
            # Venue => Events => Tickets
            selectinload(Venue.events)
            .load_only(Event.id)
            .selectinload(
                # TODO: return all tickets if user has permission from organization
                Event.tickets.and_(Ticket.account_id == user.id if user is not None else false())
            )
            .load_only(Ticket.id),
            # Venue => Organization
            selectinload(Venue.organization),
        )
    )
    return {"venues": venues.all()}


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
