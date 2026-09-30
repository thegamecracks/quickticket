import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from quickticket.dependencies.auth import RequiredUserDep

router = APIRouter(tags=["Profiles"])
log = logging.getLogger(__name__)


class ProfileAddress(BaseModel):
    address_id: UUID
    line_1: str
    line_2: str
    city: str
    province: str
    postal_code: str


class Profile(BaseModel):
    account_id: UUID
    created_at: datetime
    display_name: str
    first_name: str
    last_name: str
    email: str
    addresses: list[ProfileAddress]


@router.get("/@me")
async def profile_me(user: RequiredUserDep) -> Profile:
    """Retrieve the current user."""
    return Profile(
        account_id=user.id,
        created_at=user.created_at,
        display_name=user.display_name,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        addresses=[
            ProfileAddress(
                address_id=address.id,
                line_1=address.line_1,
                line_2=address.line_2,
                city=address.city,
                province=address.province,
                postal_code=address.postal_code,
            )
            for address in await user.awaitable_attrs.addresses
        ],
    )
