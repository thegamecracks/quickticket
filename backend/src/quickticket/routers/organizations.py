import logging
from uuid import UUID

from fastapi import APIRouter

router = APIRouter(tags=["Organizations"])
log = logging.getLogger(__name__)


@router.get("/")
async def get_organizations() -> None:
    """Get a list of organizations."""
    # TODO: support pagination


@router.get("/{organization_id}")
async def get_organization(organization_id: UUID) -> None:
    """Get an organization by ID."""
    # TODO: load organization events
    # TODO: load organization venues
    # TODO: load organization members
    # TODO: load user's tickets for organization if logged in


@router.post("/")
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
