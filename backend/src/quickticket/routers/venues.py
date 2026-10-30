import logging
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import false, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.functions import count

from quickticket.dependencies.auth import OptionalUserDep, RequiredUserDep
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.dependencies.organizations import get_organization_controller
from quickticket.models import (
    Event,
    Money,
    OrganizationMemberPermissions,
    Point,
    StorageObject,
    Ticket,
    Venue,
)

VENUE_LIMIT = 5

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

    events: list[PartialEvent]
    organization: PartialOrganization


class VenuesRead(BaseModel):
    venues: list[PartialVenue]


@router.get("", response_model=VenuesRead)
async def get_venues(
    user: OptionalUserDep,
    session: AsyncSessionDep,
    before: Annotated[
        datetime | None,
        Query(
            description="Return venues before the given datetime, exclusive.",
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            description="Limit the number of venues returned.",
            gt=0,
            le=10,
        ),
    ] = 10,
) -> Any:
    """Get a list of venues."""
    # TODO: sort by location proximity in latitude/longitude
    # TODO: maybe support FTS search?
    query = select(Venue).order_by(Venue.created_at.desc()).limit(limit)
    if before is not None:
        query = query.where(Venue.created_at < before)

    query = query.options(
        selectinload(Venue.banner).load_only(StorageObject.id),
        selectinload(Venue.thumbnail).load_only(StorageObject.id),
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

    venues = await session.scalars(query)
    return {"venues": venues.all()}


class VenueReadEvent(BaseModel):
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


class VenueRead(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str
    description: str
    theme: str
    thumbnail: PartialStorageObject | None
    banner: PartialStorageObject | None
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
            selectinload(Venue.banner).load_only(StorageObject.id),
            selectinload(Venue.thumbnail).load_only(StorageObject.id),
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


class VenueCreate(BaseModel):
    organization_id: UUID
    display_name: Annotated[str, Field(max_length=128)]
    description: Annotated[str, Field(max_length=4096)]
    theme: Annotated[str, Field(max_length=128)]
    location_name: Annotated[str, Field(max_length=128)]

    location_coords: Point | None = None
    # TODO: allow uploading banner and thumbnail in separate endpoints (see #52)
    # banner_id: UUID | None = None
    # thumbnail_id: UUID | None = None


@router.post("", response_model=VenueRead)
async def create_venue(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    venue: VenueCreate,
) -> Venue:
    """Create a new venue in an organization."""
    controller = await get_organization_controller(session, user, venue.organization_id)
    controller.assert_permissions(OrganizationMemberPermissions.ADMINISTRATOR)

    venue_count = await session.scalar(
        select(count()).where(Venue.organization_id == controller.organization.id)
    )
    assert venue_count is not None
    if venue_count >= VENUE_LIMIT:
        raise HTTPException(400, f"Reached maximum venue limit: {VENUE_LIMIT}")

    # TODO: allow venue drafts?
    venue_orm = Venue(
        organization_id=controller.organization.id,
        display_name=venue.display_name,
        description=venue.description,
        theme=venue.theme,
        location_name=venue.location_name,
        location_coords=venue.location_coords,
    )
    session.add(venue_orm)
    await session.flush()
    # Eagerly load relationships to prevent lazy read on VenueRead validation
    await session.refresh(venue_orm, ["events", "organization"])

    return venue_orm


@router.patch("/{venue_id}", deprecated=True)
async def edit_venue(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    venue_id: UUID,
) -> None:
    """Edit a venue's details."""
    # TODO: check authorization by organization
    # TODO: allow venue drafts?
    raise HTTPException(501)


@router.delete("/{venue_id}", deprecated=True)
async def delete_venue(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    venue_id: UUID,
) -> None:
    """Delete a venue."""
    # TODO: check authorization by organization
    # TODO: block venue deletion if any tickets are issued
    raise HTTPException(501)
