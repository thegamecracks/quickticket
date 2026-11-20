import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import MISSING, AwareDatetime, BaseModel
from sqlalchemy import exists, false, select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.interfaces import ORMOption
from sqlalchemy.sql.functions import count
from starlette.status import HTTP_201_CREATED

from quickticket.dependencies.auth import OptionalUserDep, RequiredUserDep
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.dependencies.models import get_organization_controller
from quickticket.models import (
    Event,
    EventID,
    Organization,
    OrganizationID,
    OrganizationMember,
    OrganizationMemberPermissions,
    StorageObject,
    StorageObjectID,
    Ticket,
    User,
    UserID,
    Venue,
    VenueID,
)
from quickticket.paging import (
    DateTimeFilterParams,
    DateTimeSortKey,
    KeysetPagedResponse,
    KeysetPageParams,
)
from quickticket.validators import DisplayNameField

router = APIRouter(tags=["Organizations"])
log = logging.getLogger(__name__)


class PartialOrganization(BaseModel):
    id: OrganizationID
    created_at: AwareDatetime
    display_name: str


@router.get("", response_model=KeysetPagedResponse[PartialOrganization, DateTimeSortKey])
async def get_organizations(
    session: AsyncSessionDep,
    page: Annotated[KeysetPageParams[DateTimeSortKey], Query()],
    dt_filter: Annotated[DateTimeFilterParams, Query()],
) -> Any:
    """Get a list of organizations."""
    query = select(Organization)

    # Insert filter conditions between here and paged_query
    if dt_filter.after is not None:
        query = query.where(Organization.created_at > dt_filter.after)
    if dt_filter.before is not None:
        query = query.where(Organization.created_at < dt_filter.before)

    paged_query = query.order_by(Organization.created_at.desc()).limit(page.limit)
    if page.next is not None:
        # NOTE: keyset pagination breaks if there are >=limit items with the same key
        paged_query = paged_query.where(Organization.created_at < page.next)

    items = await session.scalars(paged_query)
    items = items.all()
    # Next key must match order_by() clause
    next_key = None if len(items) < page.limit else items[-1].created_at
    # Is this slow?
    total = await session.scalar(query.with_only_columns(count(), maintain_column_froms=True))
    return {"items": items, "next": next_key, "total": total}


class PartialStorageObject(BaseModel):
    id: StorageObjectID


class PartialEvent(BaseModel):
    id: EventID
    created_at: AwareDatetime
    display_name: str
    description: str
    category: str
    thumbnail: PartialStorageObject | None
    banner: PartialStorageObject | None
    # starts_at: AwareDatetime
    # ends_at: AwareDatetime
    # ticket_price: Money
    # max_attendees: int


class PartialVenue(BaseModel):
    id: VenueID
    created_at: AwareDatetime
    display_name: str
    description: str
    category: str
    thumbnail: PartialStorageObject | None
    banner: PartialStorageObject | None
    # location_name: str
    # location_coords: Point | None

    events: list[PartialEvent]


class PartialOrganizationMember(BaseModel):
    user_id: UserID


class OrganizationRead(BaseModel):
    id: OrganizationID
    created_at: AwareDatetime
    display_name: str

    venues: list[PartialVenue]
    members: list[PartialOrganizationMember]


def _create_options_for_get_organization(user: User | None) -> tuple[ORMOption, ...]:
    return (
        # Organization => Venues => Events => Tickets
        selectinload(Organization.venues)
        .load_only(
            Venue.id,
            Venue.created_at,
            Venue.display_name,
            Venue.description,
            Venue.category,
        )
        .selectinload(Venue.events)
        .load_only(
            Event.id,
            Event.created_at,
            Event.display_name,
            Event.description,
            Event.category,
        )
        .selectinload(
            # TODO: return all tickets if user has permission from organization
            Event.tickets.and_(Ticket.user_id == user.id if user is not None else false()),
        )
        .load_only(Ticket.id),
        selectinload(Organization.venues, Venue.banner).load_only(StorageObject.id),
        selectinload(Organization.venues, Venue.thumbnail).load_only(StorageObject.id),
        selectinload(Organization.venues, Venue.events, Event.banner).load_only(
            StorageObject.id,
        ),
        selectinload(Organization.venues, Venue.events, Event.thumbnail).load_only(
            StorageObject.id,
        ),
        # Organization => OrganizationMembers
        selectinload(Organization.members).load_only(OrganizationMember.user_id),
    )


@router.get("/{organization_id}", response_model=OrganizationRead)
async def get_organization(
    user: OptionalUserDep,
    session: AsyncSessionDep,
    organization_id: OrganizationID,
) -> Organization:
    """Get an organization by ID."""
    organization = await session.get(
        Organization,
        organization_id,
        options=_create_options_for_get_organization(user),
    )
    if organization is None:
        raise HTTPException(404, "Not found")

    return organization


class OrganizationCreate(BaseModel):
    display_name: DisplayNameField


class OrganizationUpdate(BaseModel):
    display_name: DisplayNameField | MISSING = MISSING


@router.post(
    "",
    response_model=OrganizationRead,
    responses={HTTP_201_CREATED: {"description": "The organization was successfully created."}},
    status_code=HTTP_201_CREATED,
)
async def create_organization(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization: OrganizationCreate,
    request: Request,
    response: Response,
) -> Organization:
    """Create a new organization."""

    owns_organization = await session.scalar(
        select(
            exists().where(
                OrganizationMember.user_id == user.id,
                OrganizationMember.permissions.bitwise_and(
                    OrganizationMemberPermissions.OWNER,
                ),
            ),
        ),
    )
    if owns_organization:
        raise HTTPException(400, "Already owns an organization")

    created = Organization(
        display_name=organization.display_name,
        members=[
            OrganizationMember(
                user=user,
                permissions=OrganizationMemberPermissions.OWNER,
            ),
        ],
    )

    session.add(created)
    await session.flush()
    await session.refresh(created, ["members", "venues"])

    response.headers["Location"] = str(
        request.url_for("get_organization", organization_id=created.id),
    )
    return created


@router.patch("/{organization_id}", response_model=OrganizationRead)
async def edit_organization(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization_id: OrganizationID,
    changes: OrganizationUpdate,
) -> Organization:
    """Edit an organization's details."""
    # TODO: schedule notifications
    # TODO: allow organization drafts?
    organization = await session.get(
        Organization,
        organization_id,
        options=_create_options_for_get_organization(user),
    )
    if organization is None:
        raise HTTPException(404, "Not found")

    controller = await get_organization_controller(session, user, organization.id)
    controller.assert_permissions(OrganizationMemberPermissions.OWNER)

    if not changes.model_fields_set:
        raise HTTPException(400, "No fields to update")

    for name in changes.model_fields_set:
        setattr(organization, name, getattr(changes, name))

    return organization


@router.delete("/{organization_id}", deprecated=True)
async def delete_organization(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization_id: OrganizationID,
) -> None:
    """Delete an organization."""
    # TODO: check authorization by organization_member
    # TODO: block organization deletion if any events are active
    raise HTTPException(501)


@router.patch("/{organization_id}/{user_id}", deprecated=True)
async def edit_organization_member(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization_id: OrganizationID,
    user_id: UserID,
) -> None:
    """Edit an organization member."""
    # NOTE: not planned for release, leave empty!
    # - check authorization by organization_member
    # - schedule notifications
    # - allow organization drafts?
    raise HTTPException(501)


@router.delete("/{organization_id}/{user_id}", deprecated=True)
async def delete_organization_member(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization_id: OrganizationID,
    user_id: UserID,
) -> None:
    """Remove a member from an organization."""
    # NOTE: not planned for release, leave empty!
    # - check authorization by organization_member
    raise HTTPException(501)


@router.post("/{organization_id}/{user_id}", deprecated=True)
async def invite_organization_member(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization_id: OrganizationID,
    user_id: UserID,
) -> None:
    """Invite a user to an organization."""
    # NOTE: not planned for release, leave empty!
    # - check authorization by organization_member
    # - fail if member already exists
    # - specify permissions of accepted invite
    # - send notification to recipient
    # - prevent invite spamming? perhaps require recipient to opt-in to invites?
    raise HTTPException(501)


@router.get("/invites/{invite_id}", deprecated=True)
async def get_organization_member_invite(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization_id: OrganizationID,
    invite_id: UUID,
) -> None:
    """Get an invite for an organization."""
    # NOTE: not planned for release, leave empty!
    # - check authorization by invite recipient
    # - send notification to sender
    raise HTTPException(501)


@router.post("/invites/{invite_id}/accept", deprecated=True)
async def accept_organization_member_invite(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization_id: OrganizationID,
    invite_id: UUID,
) -> None:
    """Accept an invite for an organization."""
    # NOTE: not planned for release, leave empty!
    # - check authorization by invite recipient
    # - send notification to sender
    raise HTTPException(501)


@router.post("/invites/{invite_id}/reject", deprecated=True)
async def reject_organization_member_invite(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization_id: OrganizationID,
    invite_id: UUID,
) -> None:
    """Reject an invite for an organization."""
    # NOTE: not planned for release, leave empty!
    # - check authorization by invite recipient
    # - send notification to sender
    raise HTTPException(501)
