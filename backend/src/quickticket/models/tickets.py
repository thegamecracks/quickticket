from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid7

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.accounts import User
from quickticket.models.base import Base
from quickticket.models.money import Money
from quickticket.models.types import current_timestamp, pk_uuid

if TYPE_CHECKING:
    from quickticket.models.events import Event

__all__ = ("Ticket",)


class Ticket(Base, kw_only=True, repr=False):
    __tablename__ = "ticket"

    id: Mapped[pk_uuid] = mapped_column("ticket_id", default_factory=uuid7)

    # Required
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("event.event_id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("account.account_id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    paid_cost: Mapped[Money]

    # Optional
    created_at: Mapped[current_timestamp] = mapped_column(default=None, index=True)

    # Relationships
    event: Mapped[Event] = relationship(
        default=None,
        back_populates="tickets",
    )
    user: Mapped[User] = relationship(
        default=None,
        back_populates="tickets",
    )
