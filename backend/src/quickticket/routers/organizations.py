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
from quickticket.models import Event, Organization, OrganizationMember, Ticket, Venue

router = APIRouter(tags=["Organizations"])
log = logging.getLogger(__name__)


class PartialOrganization(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str


class OrganizationsRead(BaseModel):
    organizations: list[PartialOrganization]


@router.get("", response_model=OrganizationsRead)
async def get_organizations(session: AsyncSessionDep) -> Any:
    """Get a list of organizations."""
    # TODO: support pagination
    organizations = await session.scalars(
        select(Organization).order_by(Organization.created_at.desc())
    )
    return {"organizations": organizations.all()}


class PartialEvent(BaseModel):
    id: UUID
    created_at: datetime
    display_name: str
    description: str
    theme: str
    thumbnail_url: str
    # banner_url: str
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
    thumbnail_url: str
    # banner_url: str
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
                Venue.thumbnail_url,
            )
            .selectinload(Venue.events)
            .load_only(
                Event.id,
                Event.created_at,
                Event.display_name,
                Event.description,
                Event.theme,
                Event.thumbnail_url,
            )
            .selectinload(
                # TODO: return all tickets if user has permission from organization
                Event.tickets.and_(Ticket.account_id == user.id if user is not None else false())
            )
            .load_only(Ticket.id),
            # Organization => OrganizationMembers
            selectinload(Organization.members).load_only(OrganizationMember.account_id),
        )
    )
    if organization is None:
        raise HTTPException(404, "Not found")

    return organization


@router.post("")
async def create_organization() -> None:
    """Create a new organization."""
    # TODO: only allow one organization per user


@router.patch("/{organization_id}")
async def edit_organization(organization_id: UUID) -> None:
    """Edit an organization's details."""
    # TODO: check authorization by organization_member
    # TODO: schedule notifications
    # TODO: allow organization drafts?


@router.delete("/{organization_id}")
async def delete_organization(organization_id: UUID) -> None:
    """Delete an organization."""
    # TODO: check authorization by organization_member
    # TODO: block organization deletion if any events are active


@router.patch("/{organization_id}/{account_id}")
async def edit_organization_member(organization_id: UUID, account_id: UUID) -> None:
    """Edit an organization member."""
    # TODO: check authorization by organization_member
    # TODO: schedule notifications
    # TODO: allow organization drafts?


@router.delete("/{organization_id}/{account_id}")
async def delete_organization_member(organization_id: UUID, account_id: UUID) -> None:
    """Remove an account from an organization."""
    # TODO: check authorization by organization_member


@router.post("/{organization_id}/{account_id}")
async def invite_organization_member(organization_id: UUID, account_id: UUID) -> None:
    """Invite an account to an organization."""
    # TODO: check authorization by organization_member
    # TODO: fail if member already exists
    # TODO: specify permissions of accepted invite
    # TODO: send notification to recipient
    # TODO: prevent invite spamming? perhaps require recipient to opt-in to invites?


@router.get("/invites/{invite_id}")
async def get_organization_member_invite(organization_id: UUID, invite_id: UUID) -> None:
    """Get an invite for an organization."""
    # TODO: check authorization by invite recipient
    # TODO: send notification to sender


@router.post("/invites/{invite_id}/accept")
async def accept_organization_member_invite(organization_id: UUID, invite_id: UUID) -> None:
    """Accept an invite for an organization."""
    # TODO: check authorization by invite recipient
    # TODO: send notification to sender


@router.post("/invites/{invite_id}/reject")
async def reject_organization_member_invite(organization_id: UUID, invite_id: UUID) -> None:
    """Reject an invite for an organization."""
    # TODO: check authorization by invite recipient
    # TODO: send notification to sender
