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
from quickticket.models import Event, Money, Point, Ticket, Venue

router = APIRouter(tags=["Events"])
log = logging.getLogger(__name__)


class PartialTicket(BaseModel):
    id: UUID


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

    organization: PartialOrganization


class EventRead(BaseModel):
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
    venue: PartialVenue


class EventsRead(BaseModel):
    events: list[EventRead]


@router.get("", response_model=EventsRead)
async def get_events(user: OptionalUserDep, session: AsyncSessionDep) -> Any:
    """Get a list of events."""
    # TODO: sort by location?
    # TODO: sort by most tickets?
    # TODO: support pagination
    # TODO: maybe support FTS search?
    events = await session.scalars(
        select(Event)
        .order_by(Event.created_at.desc())
        .options(
            selectinload(Event.venue)
            .load_only(
                Venue.id,
                Venue.created_at,
                Venue.display_name,
                Venue.description,
                Venue.theme,
                Venue.thumbnail_url,
                Venue.banner_url,
                Venue.location_name,
                Venue.location_coords,
            )
            .selectinload(Venue.organization),
            selectinload(
                # TODO: return all tickets if user has permission from organization
                Event.tickets.and_(Ticket.account_id == user.id if user is not None else false())
            ).load_only(Ticket.id),
        )
    )
    return {"events": events.all()}


@router.get("/{event_id}", response_model=EventRead)
async def get_event(user: OptionalUserDep, session: AsyncSessionDep, event_id: UUID) -> Any:
    """Get an event by ID."""
    event = await session.scalar(
        select(Event)
        .where(Event.id == event_id)
        .order_by(Event.created_at.desc())
        .options(
            selectinload(Event.venue).selectinload(Venue.organization),
            selectinload(
                # TODO: return all tickets if user has permission from organization
                Event.tickets.and_(Ticket.account_id == user.id if user is not None else false())
            ).load_only(Ticket.id),
        )
    )
    if event is None:
        raise HTTPException(404, "Not found")

    return event


@router.post("")
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
