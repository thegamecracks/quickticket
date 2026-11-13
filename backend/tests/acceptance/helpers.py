"""Shared setup for venue acceptance tests."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import (
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    User,
)


def venue_body(organization_id: UUID, **overrides: Any) -> dict[str, Any]:
    """A complete physical-venue payload. Override keys to target one rule."""
    body: dict[str, Any] = {
        "organization_id": str(organization_id),
        "display_name": "Harbour Hall",
        "description": "A waterfront room with seating for 120.",
        "theme": "Music",
        "location_name": "88 Granville St., Toronto",
        "location_coords": {"lat": 43.6532, "long": -79.3832},
    }
    body.update(overrides)
    return body


async def make_administrator(
    make_session: async_sessionmaker[AsyncSession],
    user: User,
    *,
    display_name: str = "Harbour Hall Organizers",
) -> Organization:
    """Create an organization the signed-in user administers."""
    async with make_session.begin() as session:
        organization = Organization(display_name=display_name)
        member = OrganizationMember(
            organization_id=organization.id,
            account_id=user.id,
            permissions=OrganizationMemberPermissions.ADMINISTRATOR,
        )
        session.add_all([organization, member])
    return organization
