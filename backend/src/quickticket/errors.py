from fastapi import Response

from quickticket.models import (
    Base,
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    User,
)


class ForcedResponse(Exception):
    """The application must return the given response.

    This allows interrupting the flow of execution from outside route functions,
    for example when a dependency needs to prompt the user to re-authenticate.

    """

    def __init__(self, response: Response) -> None:
        self.response = response


class EntityNotFound(Exception):
    """A required entity was not found."""


class ORMEntityNotFound(EntityNotFound):
    """A required ORM entity was not found."""

    def __init__(self, entity: type[Base], ident: object | tuple[object, ...]) -> None:
        super().__init__(f"{entity.__name__} not found: {ident}")
        self.entity = entity
        self.ident = ident


class OrganizationMemberNotFound(EntityNotFound):
    """A user is not a member of an organization."""

    def __init__(self, organization: Organization, user: User) -> None:
        super().__init__(f"User ({user.id}) is not a member of organization ({organization.id})")
        self.organization = organization
        self.user = user


class UnauthorizedError(Exception):
    """An entity is not permitted to perform an operation."""


class UnauthorizedUser(UnauthorizedError):
    """An account is not permitted to perform an operation."""

    def __init__(self, user: User) -> None:
        super().__init__(f"User ({user.id}) is unauthorized")
        self.user = user


class UnauthorizedOrganizationMember(UnauthorizedError):
    """An organization member is not permitted to perform an operation."""

    def __init__(self, member: OrganizationMember, required: OrganizationMemberPermissions) -> None:
        self.member = member
        self.required = required
        super().__init__(
            f"Organization member ({member.organization_id, member.account_id}) "
            f"missing permissions: {', '.join(m._name_ for m in self.missing)}"
        )

    @property
    def missing(self) -> OrganizationMemberPermissions:
        return self.required & ~self.member.permissions
