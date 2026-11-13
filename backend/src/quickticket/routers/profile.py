import logging

from fastapi import APIRouter
from pydantic import AwareDatetime, BaseModel

from quickticket.dependencies.auth import RequiredUserDep
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.models import (
    AddressID,
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


class Profile(BaseModel):
    id: UserID
    created_at: AwareDatetime
    display_name: str
    first_name: str
    last_name: str
    email: str
    addresses: list[ProfileAddress]


@router.get("/@me", response_model=Profile)
async def profile_me(session: AsyncSessionDep, user: RequiredUserDep) -> User:
    """Retrieve the current user."""
    await session.refresh(user, ["addresses"])
    return user
