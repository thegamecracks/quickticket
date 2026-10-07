import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import false, select
from sqlalchemy.orm import selectinload

from quickticket.dependencies.auth import OptionalUserDep
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.models import Event, Point, Ticket, Venue
from quickticket.models.money import Money

router = APIRouter(tags=["Venues"])
log = logging.getLogger(__name__)


class PartialTicket(BaseModel):
    id: UUID


class PartialEvent(BaseModel):
    id: UUID
    tickets: list[PartialTicket]


class PartialOrganization(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str


class PartialVenue(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str
    description: str
    theme: str
    thumbnail_url: str
    banner_url: str
    location_name: str
    location_coords: Point | None

    events: list[PartialEvent]
    organization: PartialOrganization


class VenuesRead(BaseModel):
    venues: list[PartialVenue]


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


class VenueReadEvent(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str
    description: str
    theme: str
    thumbnail_url: str
    banner_url: str
    starts_at: datetime
    ends_at: datetime
    ticket_price: Money
    max_attendees: int

    tickets: list[PartialTicket]


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
    organization: PartialOrganization


@router.get("/{venue_id}", response_model=VenueRead)
async def get_venue(user: OptionalUserDep, session: AsyncSessionDep, venue_id: UUID) -> Any:
    """Get a venue by ID."""
    venue = await session.scalar(
        select(Venue)
        .where(Venue.id == venue_id)
        .options(
            # Venue => Events => Tickets
            selectinload(Venue.events)
            .selectinload(
                # TODO: return all tickets if user has permission from organization
                Event.tickets.and_(Ticket.account_id == user.id if user is not None else false())
            )
            .load_only(Ticket.id),
            # Venue => Organization
            selectinload(Venue.organization),
        )
    )
    if venue is None:
        raise HTTPException(404, "Not found")

    return venue


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
