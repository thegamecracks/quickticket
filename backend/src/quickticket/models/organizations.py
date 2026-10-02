from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.accounts import User
from quickticket.models.base import Base
from quickticket.models.types import current_timestamp, str_128

if TYPE_CHECKING:
    from quickticket.models.events import Venue

__all__ = (
    "Organization",
    "OrganizationMember",
)


class Organization(Base):
    __tablename__ = "organization"

    id: Mapped[UUID] = mapped_column("organization_id", primary_key=True)
    created_at: Mapped[current_timestamp]
    display_name: Mapped[str_128]

    members: Mapped[list[OrganizationMember]] = relationship(back_populates="organization")
    venues: Mapped[list[Venue]] = relationship(back_populates="organization")


class OrganizationMember(Base):
    __tablename__ = "organization_member"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organization.organization_id"),
        primary_key=True,
    )
    acccount_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.account_id"),
        primary_key=True,
    )
    joined_at: Mapped[current_timestamp]
    permissions: Mapped[int]  # TODO: OrganizationMemberPermissions(IntFlag)

    organization: Mapped[Organization] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="organization_members")
