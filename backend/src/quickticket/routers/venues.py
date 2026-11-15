import logging
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import AfterValidator, AwareDatetime, BaseModel, Field
from sqlalchemy import false, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.functions import count
from starlette.status import HTTP_201_CREATED

from quickticket.dependencies.auth import OptionalUserDep, RequiredUserDep
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.dependencies.models import get_organization_controller
from quickticket.models import (
    Event,
    EventID,
    Money,
    OrganizationID,
    OrganizationMemberPermissions,
    Point,
    StorageObject,
    StorageObjectID,
    Ticket,
    TicketID,
    Venue,
    VenueID,
)
from quickticket.paging import (
    DateTimeFilterParams,
    DateTimeSortKey,
    KeysetPagedResponse,
    KeysetPageParams,
)
from quickticket.routers.images import create_banner_routes, create_thumbnail_routes
from quickticket.validators import DisplayNameField, filter_string_field

VENUE_LIMIT = 5

router = APIRouter(tags=["Venues"])
log = logging.getLogger(__name__)


class PartialTicket(BaseModel):
    id: TicketID


class PartialEvent(BaseModel):
    id: EventID
    tickets: list[PartialTicket]


class PartialOrganization(BaseModel):
    id: OrganizationID
    created_at: AwareDatetime
    display_name: str


class PartialStorageObject(BaseModel):
    id: StorageObjectID


class PartialVenue(BaseModel):
    id: VenueID
    created_at: AwareDatetime
    display_name: str
    description: str
    theme: str
    thumbnail: PartialStorageObject | None
    banner: PartialStorageObject | None
    location_name: str
    location_coords: Point | None

    events: list[PartialEvent]
    organization: PartialOrganization


@router.get("", response_model=KeysetPagedResponse[PartialVenue, DateTimeSortKey])
async def get_venues(
    user: OptionalUserDep,
    session: AsyncSessionDep,
    page: Annotated[KeysetPageParams[DateTimeSortKey], Query()],
    dt_filter: Annotated[DateTimeFilterParams, Query()],
) -> Any:
    """Get a list of venues."""
    # TODO: sort by location proximity in latitude/longitude
    # TODO: maybe support FTS search?
    query = select(Venue)

    # Insert filter conditions between here and paged_query
    if dt_filter.after is not None:
        query = query.where(Venue.created_at > dt_filter.after)
    if dt_filter.before is not None:
        query = query.where(Venue.created_at < dt_filter.before)

    paged_query = query.order_by(Venue.created_at.desc()).limit(page.limit)
    if page.next is not None:
        # NOTE: keyset pagination breaks if there are >=limit items with the same key
        paged_query = paged_query.where(Venue.created_at < page.next)

    paged_query = paged_query.options(
        selectinload(Venue.banner).load_only(StorageObject.id),
        selectinload(Venue.thumbnail).load_only(StorageObject.id),
        # Venue => Events => Tickets
        selectinload(Venue.events)
        .load_only(Event.id)
        .selectinload(
            # TODO: return all tickets if user has permission from organization
            Event.tickets.and_(Ticket.account_id == user.id if user is not None else false()),
        )
        .load_only(Ticket.id),
        # Venue => Organization
        selectinload(Venue.organization),
    )

    items = await session.scalars(paged_query)
    items = items.all()
    # Next key must match order_by() clause
    next_key = None if len(items) < page.limit else items[-1].created_at
    # Is this slow?
    total = await session.scalar(query.with_only_columns(count(), maintain_column_froms=True))
    return {"items": items, "next": next_key, "total": total}


class VenueReadEvent(BaseModel):
    id: VenueID
    created_at: AwareDatetime
    display_name: str
    description: str
    theme: str
    thumbnail: PartialStorageObject | None
    banner: PartialStorageObject | None
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    ticket_price: Money
    max_attendees: int

    tickets: list[PartialTicket]


class VenueRead(BaseModel):
    id: VenueID
    created_at: AwareDatetime
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
async def get_venue(user: OptionalUserDep, session: AsyncSessionDep, venue_id: VenueID) -> Any:
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
                Event.tickets.and_(Ticket.account_id == user.id if user is not None else false()),
            )
            .load_only(Ticket.id),
            # Venue => Organization
            selectinload(Venue.organization),
        ),
    )
    if venue is None:
        raise HTTPException(404, "Not found")

    return venue


class VenueCreate(BaseModel):
    organization_id: OrganizationID
    display_name: DisplayNameField
    description: Annotated[str, AfterValidator(filter_string_field), Field(max_length=4096)]
    theme: Annotated[str, AfterValidator(filter_string_field), Field(max_length=128)]
    location_name: Annotated[str, AfterValidator(filter_string_field), Field(max_length=128)]

    location_coords: Point | None = None


@router.post(
    "",
    response_model=VenueRead,
    responses={HTTP_201_CREATED: {"description": "The venue was successfully created."}},
    status_code=HTTP_201_CREATED,
)
async def create_venue(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    venue: VenueCreate,
    request: Request,
    response: Response,
) -> Venue:
    """Create a new venue in an organization."""
    controller = await get_organization_controller(session, user, venue.organization_id)
    controller.assert_permissions(OrganizationMemberPermissions.ADMINISTRATOR)

    venue_count = await session.scalar(
        select(count()).where(Venue.organization_id == controller.organization.id),
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

    response.headers["Location"] = str(request.url_for("get_venue", venue_id=venue_orm.id))
    return venue_orm


@router.patch("/{venue_id}", deprecated=True)
async def edit_venue(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    venue_id: VenueID,
) -> None:
    """Edit a venue's details."""
    # TODO: check authorization by organization
    # TODO: allow venue drafts?
    raise HTTPException(501)


@router.delete("/{venue_id}", deprecated=True)
async def delete_venue(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    venue_id: VenueID,
) -> None:
    """Delete a venue."""
    # TODO: check authorization by organization
    # TODO: block venue deletion if any tickets are issued
    raise HTTPException(501)


router.include_router(
    create_banner_routes(
        Venue,
        get_organization_id=lambda venue: venue.organization_id,
        options=(),
    ),
)
router.include_router(
    create_thumbnail_routes(
        Venue,
        get_organization_id=lambda venue: venue.organization_id,
        options=(),
    ),
)
