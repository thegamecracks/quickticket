import logging
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import false, select
from sqlalchemy.orm import selectinload

from quickticket.dependencies.auth import OptionalUserDep, RequiredUserDep
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.dependencies.organizations import get_organization_controller
from quickticket.errors import ORMEntityNotFound
from quickticket.models import Event, Money, Point, StorageObject, Ticket, Venue
from quickticket.models.organizations import OrganizationMemberPermissions

router = APIRouter(tags=["Events"])
log = logging.getLogger(__name__)


class PartialTicket(BaseModel):
    id: UUID


class PartialOrganization(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str


class PartialStorageObject(BaseModel):
    id: UUID


class PartialVenue(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str
    description: str
    theme: str
    thumbnail: PartialStorageObject | None
    banner: PartialStorageObject | None
    location_name: str
    location_coords: Point | None

    organization: PartialOrganization


class EventRead(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str
    description: str
    theme: str
    thumbnail: PartialStorageObject | None
    banner: PartialStorageObject | None
    starts_at: datetime
    ends_at: datetime
    ticket_price: Money
    max_attendees: int

    tickets: list[PartialTicket]
    venue: PartialVenue


class EventsRead(BaseModel):
    events: list[EventRead]


@router.get("", response_model=EventsRead)
async def get_events(
    user: OptionalUserDep,
    session: AsyncSessionDep,
    before: Annotated[
        datetime | None,
        Query(
            description="Return events before the given datetime, exclusive.",
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            description="Limit the number of events returned.",
            gt=0,
            le=10,
        ),
    ] = 10,
) -> Any:
    """Get a list of events."""
    # TODO: sort by location?
    # TODO: sort by most tickets?
    # TODO: maybe support FTS search?
    query = select(Event).order_by(Event.created_at.desc()).limit(limit)
    if before is not None:
        query = query.where(Event.created_at < before)

    query = query.options(
        selectinload(Event.banner).load_only(StorageObject.id),
        selectinload(Event.thumbnail).load_only(StorageObject.id),
        selectinload(Event.venue).load_only(
            Venue.id,
            Venue.created_at,
            Venue.display_name,
            Venue.description,
            Venue.theme,
            Venue.location_name,
            Venue.location_coords,
        ),
        selectinload(Event.venue, Venue.banner).load_only(StorageObject.id),
        selectinload(Event.venue, Venue.thumbnail).load_only(StorageObject.id),
        selectinload(Event.venue, Venue.organization),
        selectinload(
            # TODO: return all tickets if user has permission from organization
            Event.tickets.and_(Ticket.account_id == user.id if user is not None else false())
        ).load_only(Ticket.id),
    )

    events = await session.scalars(query)
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


class EventCreate(BaseModel):
    venue_id: UUID
    display_name: str
    description: str
    theme: str
    starts_at: datetime
    ends_at: datetime

    max_attendees: int
    ticket_price: Money
    # ! TODO: implement thumbnails & banner support
    # banner_id: UUID | None = None
    # thumbnail_id: UUID | None = None

    # tickets: list[PartialTicket]
    # venue: PartialVenue


@router.post("", response_model=EventRead)
async def create_event(
    user: RequiredUserDep, session: AsyncSessionDep, event: EventCreate
) -> Event:
    """Create a new event for a venue."""
    # TODO: check authorization by organization
    # TODO: schedule notifications
    # TODO: allow event drafts?

    # get venue from event object to validate permissions in controller
    nestedVenue = await session.scalar(
        select(Venue).where(Venue.id == event.venue_id).options(selectinload(Venue.organization))
    )
    if nestedVenue is None:
        raise ORMEntityNotFound(Venue, event.venue_id)

    controller = await get_organization_controller(session, user, nestedVenue.organization_id)
    controller.assert_permissions(OrganizationMemberPermissions.ADMINISTRATOR)

    # ! TODO: add banner, thumbnail
    event_orm = Event(
        display_name=event.display_name,
        description=event.description,
        venue_id=event.venue_id,
        starts_at=event.starts_at,
        ends_at=event.ends_at,
        theme=event.theme,
        ticket_price=event.ticket_price,
        max_attendees=event.max_attendees,
    )
    session.add(event_orm)
    await session.flush()
    await session.refresh(event_orm, ["tickets", "venue"])
    return event_orm


@router.patch("/{event_id}", deprecated=True)
async def edit_event(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    event_id: UUID,
) -> None:
    """Edit an event's details."""
    # TODO: check authorization by organization
    # TODO: schedule notifications
    # TODO: allow event drafts?
    raise HTTPException(501)


@router.delete("/{event_id}", deprecated=True)
async def delete_event(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    event_id: UUID,
) -> None:
    """Delete an event."""
    # TODO: check authorization by organization
    # TODO: block event deletion if any tickets are issued
    raise HTTPException(501)
