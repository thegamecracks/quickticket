from collections.abc import Collection

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


class UnauthorizedError(Exception):
    """An entity is not permitted to perform an operation."""


class OrganizationMemberNotFound(UnauthorizedError):
    """A user is not a member of an organization."""

    def __init__(self, organization: Organization, user: User) -> None:
        super().__init__(f"User ({user.id}) is not a member of organization ({organization.id})")
        self.organization = organization
        self.user = user


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
            f"Organization member ({member.organization_id}, {member.account_id}) "
            f"missing permissions: {', '.join(m._name_ for m in self.missing)}",
        )

    @property
    def missing(self) -> OrganizationMemberPermissions:
        return self.required & ~self.member.permissions


class FileProcessingError(Exception):
    """An input file cannot be processed."""


class ImageAnimationNotAccepted(FileProcessingError):
    """The image cannot be animated."""

    def __init__(self) -> None:
        super().__init__("Animated image not accepted")


class ImageFormatNotAccepted(FileProcessingError):
    """The image filetype does not match the accepted image formats."""

    def __init__(self, content_type: str | None, accepted: Collection[str]) -> None:
        self.content_type = content_type
        self.accepted = accepted
        super().__init__(f"Image format not accepted: {content_type}")


class FileSizeTooSmall(FileProcessingError):
    """The file's size is below the minimum filesize allowed."""

    def __init__(self, filesize: int, min_filesize: int) -> None:
        self.filesize = filesize
        self.min_filesize = min_filesize
        super().__init__(f"File size too small: {filesize:,d}B < {min_filesize:,d}B")

    @classmethod
    def raise_if_below(cls, filesize: int | None, *, min_filesize: int) -> None:
        # Intentional keyword-only parameter to avoid mis-ordering arguments
        if filesize is None:
            raise cls(0, min_filesize)
        if filesize < min_filesize:
            raise cls(filesize, min_filesize)


class FileSizeExceeded(FileProcessingError):
    """The file's size exceeds the maximum filesize allowed."""

    def __init__(self, filesize: int, max_filesize: int) -> None:
        self.filesize = filesize
        self.max_filesize = max_filesize
        super().__init__(f"File size exceeded: {filesize:,d}B > {max_filesize:,d}B")

    @classmethod
    def raise_if_above(cls, filesize: int | None, *, max_filesize: int) -> None:
        # Intentional keyword-only parameter to avoid mis-ordering arguments
        if filesize is None:
            raise cls(0, max_filesize)
        if filesize > max_filesize:
            raise cls(filesize, max_filesize)
