import logging
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import exists, false, select
from sqlalchemy.orm import selectinload

from quickticket.dependencies.auth import OptionalUserDep, RequiredUserDep
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.models import (
    Event,
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    StorageObject,
    Ticket,
    Venue,
)

router = APIRouter(tags=["Organizations"])
log = logging.getLogger(__name__)


class PartialOrganization(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str


class OrganizationsRead(BaseModel):
    organizations: list[PartialOrganization]


@router.get("", response_model=OrganizationsRead)
async def get_organizations(
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
    """Get a list of organizations."""
    query = select(Organization).order_by(Organization.created_at.desc()).limit(limit)
    if before is not None:
        query = query.where(Organization.created_at < before)

    organizations = await session.scalars(query)
    return {"organizations": organizations.all()}


class PartialStorageObject(BaseModel):
    id: UUID


class PartialEvent(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str
    description: str
    theme: str
    thumbnail: PartialStorageObject | None
    banner: PartialStorageObject | None
    # starts_at: datetime
    # ends_at: datetime
    # ticket_price: Money
    # max_attendees: int


class PartialVenue(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str
    description: str
    theme: str
    thumbnail: PartialStorageObject | None
    banner: PartialStorageObject | None
    # location_name: str
    # location_coords: Point | None

    events: list[PartialEvent]


class PartialOrganizationMember(BaseModel):
    account_id: UUID


class OrganizationRead(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str

    venues: list[PartialVenue]
    members: list[PartialOrganizationMember]


@router.get("/{organization_id}", response_model=OrganizationRead)
async def get_organization(
    user: OptionalUserDep,
    session: AsyncSessionDep,
    organization_id: UUID,
) -> Any:
    """Get an organization by ID."""
    organization = await session.scalar(
        select(Organization)
        .where(Organization.id == organization_id)
        .options(
            # Organization => Venues => Events => Tickets
            selectinload(Organization.venues)
            .load_only(
                Venue.id,
                Venue.created_at,
                Venue.display_name,
                Venue.description,
                Venue.theme,
            )
            .selectinload(Venue.events)
            .load_only(
                Event.id,
                Event.created_at,
                Event.display_name,
                Event.description,
                Event.theme,
            )
            .selectinload(
                # TODO: return all tickets if user has permission from organization
                Event.tickets.and_(Ticket.account_id == user.id if user is not None else false())
            )
            .load_only(Ticket.id),
            selectinload(Organization.venues, Venue.banner).load_only(StorageObject.id),
            selectinload(Organization.venues, Venue.thumbnail).load_only(StorageObject.id),
            selectinload(Organization.venues, Venue.events, Event.banner).load_only(
                StorageObject.id
            ),
            selectinload(Organization.venues, Venue.events, Event.thumbnail).load_only(
                StorageObject.id
            ),
            # Organization => OrganizationMembers
            selectinload(Organization.members).load_only(OrganizationMember.account_id),
        )
    )
    if organization is None:
        raise HTTPException(404, "Not found")

    return organization


class OrganizationCreate(BaseModel):
    display_name: Annotated[str, Field(min_length=1, max_length=128)]


@router.post("", response_model=OrganizationRead)
async def create_organization(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization: OrganizationCreate,
) -> Any:
    """Create a new organization."""

    # HACK: in a future release an organization might allow multiple administrators.
    #       perhaps the flag should be renamed to OWNER?
    owns_organization = await session.scalar(
        select(
            exists().where(
                OrganizationMember.account_id == user.id,
                OrganizationMember.permissions.bitwise_and(
                    OrganizationMemberPermissions.ADMINISTRATOR
                ),
            )
        )
    )
    if owns_organization:
        raise HTTPException(400, "Already owns an organization")

    created = Organization(
        display_name=organization.display_name,
        members=[
            OrganizationMember(
                user=user,
                permissions=OrganizationMemberPermissions.ADMINISTRATOR,
            ),
        ],
    )

    session.add(created)
    await session.flush()
    await session.refresh(created, ["members", "venues"])

    return created


@router.patch("/{organization_id}", deprecated=True)
async def edit_organization(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization_id: UUID,
) -> None:
    """Edit an organization's details."""
    # TODO: check authorization by organization_member
    # TODO: schedule notifications
    # TODO: allow organization drafts?
    raise HTTPException(501)


@router.delete("/{organization_id}", deprecated=True)
async def delete_organization(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization_id: UUID,
) -> None:
    """Delete an organization."""
    # TODO: check authorization by organization_member
    # TODO: block organization deletion if any events are active
    raise HTTPException(501)


@router.patch("/{organization_id}/{account_id}", deprecated=True)
async def edit_organization_member(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization_id: UUID,
    account_id: UUID,
) -> None:
    """Edit an organization member."""
    # NOTE: not planned for release, leave empty!
    # - check authorization by organization_member
    # - schedule notifications
    # - allow organization drafts?
    raise HTTPException(501)


@router.delete("/{organization_id}/{account_id}", deprecated=True)
async def delete_organization_member(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization_id: UUID,
    account_id: UUID,
) -> None:
    """Remove an account from an organization."""
    # NOTE: not planned for release, leave empty!
    # - check authorization by organization_member
    raise HTTPException(501)


@router.post("/{organization_id}/{account_id}", deprecated=True)
async def invite_organization_member(
    user: RequiredUserDep,
    session: AsyncSessionDep,
    organization_id: UUID,
    account_id: UUID,
) -> None:
    """Invite an account to an organization."""
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
    organization_id: UUID,
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
    organization_id: UUID,
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
    organization_id: UUID,
    invite_id: UUID,
) -> None:
    """Reject an invite for an organization."""
    # NOTE: not planned for release, leave empty!
    # - check authorization by invite recipient
    # - send notification to sender
    raise HTTPException(501)
