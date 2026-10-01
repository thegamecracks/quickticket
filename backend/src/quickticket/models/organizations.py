from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from quickticket.models.base import Base
from quickticket.models.types import str_128, timestamp


class Organization(Base):
    __tablename__ = "organization"

    id: Mapped[UUID] = mapped_column("organization_id", primary_key=True)
    created_at: Mapped[timestamp]
    display_name: Mapped[str_128]


class OrganizationMember(Base):
    __tablename__ = "organization_member"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organization.organization_id"), primary_key=True
    )
    acccount_id: Mapped[UUID] = mapped_column(ForeignKey("account.account_id"), primary_key=True)
    created_at: Mapped[timestamp]
    permissions: Mapped[int]  # ! todo: make sure this is 128 bit
