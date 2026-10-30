from __future__ import annotations

from enum import IntFlag
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.accounts import User
from quickticket.models.base import Base
from quickticket.models.types import current_timestamp, pk_uuid, str_128

if TYPE_CHECKING:
    from quickticket.models.events import Venue

__all__ = (
    "Organization",
    "OrganizationMember",
    "OrganizationMemberPermissions",
)


class Organization(Base, kw_only=True, repr=False):
    __tablename__ = "organization"

    id: Mapped[pk_uuid] = mapped_column("organization_id", default_factory=uuid4)

    # Required
    display_name: Mapped[str_128]

    # Optional
    created_at: Mapped[current_timestamp] = mapped_column(default=None, index=True)

    # Relationships
    members: Mapped[list[OrganizationMember]] = relationship(
        default_factory=list,
        back_populates="organization",
    )
    venues: Mapped[list[Venue]] = relationship(
        default_factory=list,
        back_populates="organization",
    )


class OrganizationMemberPermissions(IntFlag):
    ADMINISTRATOR = 1


class OrganizationMember(Base, kw_only=True, repr=False):
    __tablename__ = "organization_member"

    # Required
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organization.organization_id", ondelete="CASCADE"),
        default=None,
        primary_key=True,
    )
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.account_id", ondelete="CASCADE"),
        default=None,
        primary_key=True,
        index=True,
    )
    permissions: Mapped[OrganizationMemberPermissions] = mapped_column(
        BigInteger,
        default=OrganizationMemberPermissions(0),
    )

    # Optional
    joined_at: Mapped[current_timestamp] = mapped_column(default=None)

    # Relationships
    organization: Mapped[Organization] = relationship(
        default=None,
        back_populates="members",
    )
    user: Mapped[User] = relationship(
        default=None,
        back_populates="organization_members",
    )
