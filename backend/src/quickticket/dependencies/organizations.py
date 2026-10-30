from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from quickticket.errors import (
    OrganizationMemberNotFound,
    ORMEntityNotFound,
    UnauthorizedOrganizationMember,
)
from quickticket.models import Organization, OrganizationMember, OrganizationMemberPermissions, User

__all__ = (
    "OrganizationController",
    "get_organization_controller",
)


@dataclass(kw_only=True)
class OrganizationController:
    organization: Organization
    member: OrganizationMember
    user: User

    def assert_permissions(self, required: OrganizationMemberPermissions) -> bool:
        missing = required & ~self.member.permissions
        if missing:
            raise UnauthorizedOrganizationMember(self.member, required)
        return True


async def get_organization_controller(
    session: AsyncSession,
    user: User,
    organization_id: UUID,
) -> OrganizationController:
    organization = await session.get(Organization, organization_id)
    if organization is None:
        raise ORMEntityNotFound(Organization, organization_id)

    member_key = (organization_id, user.id)
    member = await session.get(OrganizationMember, member_key)
    if member is None:
        raise OrganizationMemberNotFound(organization, user)

    return OrganizationController(
        organization=organization,
        member=member,
        user=user,
    )
