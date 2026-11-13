import logging
from datetime import timedelta
from typing import Annotated, Any, ClassVar, Self

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import AfterValidator, AwareDatetime, BaseModel, Field, model_validator
from sqlalchemy import false, select
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.functions import count
from starlette.status import HTTP_201_CREATED

from quickticket.dependencies.auth import OptionalUserDep, RequiredUserDep
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.dependencies.models import get_organization_controller
from quickticket.errors import ORMEntityNotFound
from quickticket.models import (
    Event,
    EventID,
    Money,
    Organization,
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
from quickticket.validators import (
    DisplayNameField,
    FutureAwareDatetime,
    filter_string_field,
)

router = APIRouter(tags=["Events"])
log = logging.getLogger(__name__)


class PartialTicket(BaseModel):
    id: TicketID


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

    organization: PartialOrganization


class EventRead(BaseModel):
    id: EventID
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
    venue: PartialVenue


@router.get("", response_model=KeysetPagedResponse[EventRead, DateTimeSortKey])
async def get_events(
    user: OptionalUserDep,
    session: AsyncSessionDep,
    page: Annotated[KeysetPageParams[DateTimeSortKey], Query()],
    dt_filter: Annotated[DateTimeFilterParams, Query()],
    organization_id: Annotated[
        OrganizationID | None,
        Query(
            description=(
                "Filter events by organization ID. Nonexistent organizations return an empty list."
            ),
        ),
    ] = None,
) -> Any:
    """Get a list of events."""
    # TODO: sort by location?
    # TODO: sort by most tickets?
    # TODO: maybe support FTS search?
    query = select(Event)

    # Insert filter conditions between here and paged_query
    if dt_filter.after is not None:
        query = query.where(Event.created_at > dt_filter.after)
    if dt_filter.before is not None:
        query = query.where(Event.created_at < dt_filter.before)
    if organization_id is not None:
        query = (
            query.join(Event.venue)
            .join(Venue.organization)
            .where(Organization.id == organization_id)
        )

    paged_query = query.order_by(Event.created_at.desc()).limit(page.limit)
    if page.next is not None:
        # NOTE: keyset pagination breaks if there are >=limit items with the same key
        paged_query = paged_query.where(Event.created_at < page.next)

    paged_query = paged_query.options(
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
            Event.tickets.and_(Ticket.account_id == user.id if user is not None else false()),
        ).load_only(Ticket.id),
    )

    items = await session.scalars(paged_query)
    items = items.all()
    # Next key must match order_by() clause
    next_key = None if len(items) < page.limit else items[-1].created_at
    # Is this slow?
    total = await session.scalar(query.with_only_columns(count(), maintain_column_froms=True))
    return {"items": items, "next": next_key, "total": total}


@router.get("/{event_id}", response_model=EventRead)
async def get_event(user: OptionalUserDep, session: AsyncSessionDep, event_id: EventID) -> Any:
    """Get an event by ID."""
    event = await session.scalar(
        select(Event)
        .where(Event.id == event_id)
        .options(
            selectinload(Event.venue).selectinload(Venue.organization),
            selectinload(
                # TODO: return all tickets if user has permission from organization
                Event.tickets.and_(Ticket.account_id == user.id if user is not None else false()),
            ).load_only(Ticket.id),
        ),
    )
    if event is None:
        raise HTTPException(404, "Not found")

    return event


class EventCreate(BaseModel):
    venue_id: VenueID
    display_name: DisplayNameField
    description: Annotated[str, AfterValidator(filter_string_field), Field(max_length=4096)]
    theme: Annotated[str, AfterValidator(filter_string_field), Field(max_length=128)]
    starts_at: FutureAwareDatetime
    ends_at: FutureAwareDatetime

    max_attendees: Annotated[int, Field(ge=0, le=10000)]
    ticket_price: Money
    # ! TODO: implement thumbnails & banner support
    # banner_id: StorageObjectID | None = None
    # thumbnail_id: StorageObjectID | None = None

    MIN_DURATION: ClassVar[timedelta] = timedelta(hours=1)
    MAX_DURATION: ClassVar[timedelta] = timedelta(days=7)

    @model_validator(mode="after")
    def check_event_duration(self) -> Self:
        duration = self.ends_at - self.starts_at
        if duration < timedelta():
            raise ValueError("starts_at must be before ends_at")
        if not self.MIN_DURATION <= duration <= self.MAX_DURATION:
            raise ValueError(
                f"Event duration must be between {self.MIN_DURATION} and {self.MAX_DURATION}",
            )
        return self


@router.post(
    "",
    response_model=EventRead,
    responses={HTTP_201_CREATED: {"description": "The event was successfully created."}},
    status_code=HTTP_201_CREATED,
)
async def create_event(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    event: EventCreate,
    request: Request,
    response: Response,
) -> Event:
    """Create a new event for a venue."""
    # TODO: schedule notifications
    # TODO: allow event drafts?

    # get venue from event object to validate permissions in controller
    venue = await session.get(Venue, event.venue_id, options=[selectinload(Venue.organization)])
    if venue is None:
        raise ORMEntityNotFound(Venue, event.venue_id)

    controller = await get_organization_controller(session, user, venue.organization_id)
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

    response.headers["Location"] = str(request.url_for("get_event", event_id=event_orm.id))
    return event_orm


@router.patch("/{event_id}", deprecated=True)
async def edit_event(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    event_id: EventID,
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
    event_id: EventID,
) -> None:
    """Delete an event."""
    # TODO: check authorization by organization
    # TODO: block event deletion if any tickets are issued
    raise HTTPException(501)


router.include_router(
    create_banner_routes(
        Event,
        get_organization_id=lambda event: event.venue.organization_id,
        options=(selectinload(Event.venue),),
    ),
)
router.include_router(
    create_thumbnail_routes(
        Event,
        get_organization_id=lambda event: event.venue.organization_id,
        options=(selectinload(Event.venue),),
    ),
)
