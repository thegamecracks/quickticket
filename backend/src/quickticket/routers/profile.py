import logging

from fastapi import APIRouter
from pydantic import AwareDatetime, BaseModel

from quickticket.dependencies.auth import RequiredUserDep
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.models import (
    Address,
    AddressID,
    OrganizationID,
    OrganizationMember,
    OrganizationMemberPermissions,
    User,
    UserID,
)

router = APIRouter(tags=["Profiles"])
log = logging.getLogger(__name__)


class ProfileAddress(BaseModel):
    id: AddressID
    line_1: str
    line_2: str
    city: str
    province: str
    postal_code: str


class ProfileOrganizationMember(BaseModel):
    organization_id: OrganizationID
    user_id: UserID
    permissions: OrganizationMemberPermissions
    joined_at: AwareDatetime


class Profile(BaseModel):
    id: UserID
    created_at: AwareDatetime
    display_name: str
    first_name: str
    last_name: str
    email: str


@router.get("/@me", response_model=Profile)
async def profile_me(user: RequiredUserDep) -> User:
    """Retrieve the current user."""
    return user


@router.get("/@me/addresses", response_model=list[ProfileAddress])
async def profile_addresses(session: AsyncSessionDep, user: RequiredUserDep) -> list[Address]:
    """Retrieve the user's addresses."""
    await session.refresh(user, ["addresses"])
    return user.addresses


@router.get("/@me/organizations/members", response_model=list[ProfileOrganizationMember])
async def profile_organization_members(
    session: AsyncSessionDep,
    user: RequiredUserDep,
) -> list[OrganizationMember]:
    """Retrieve the user's organization members."""
    await session.refresh(user, ["organization_members"])
    return user.organization_members
