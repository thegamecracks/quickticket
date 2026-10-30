from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.base import Base
from quickticket.models.types import (
    current_timestamp,
    pk_uuid,
    str_2000,
)

__all__ = (
    "StorageObject",
    "StorageProvider",
)


class StorageProvider(Base, kw_only=True, repr=False):
    __tablename__ = "storage_provider"
    __table_args__ = (UniqueConstraint("endpoint", "region"),)

    id: Mapped[pk_uuid] = mapped_column("storage_provider_id", default_factory=uuid4)

    # Required
    endpoint: Mapped[str_2000]
    region: Mapped[str_2000]
    bucket: Mapped[str_2000]
    cdn_base_url: Mapped[str_2000]

    # Optional
    created_at: Mapped[current_timestamp] = mapped_column(default=None)

    # Relationships
    storage_objects: Mapped[list[StorageObject]] = relationship(
        default_factory=list,
        back_populates="provider",
    )


class StorageObject(Base, kw_only=True, repr=False):
    __tablename__ = "storage_object"

    id: Mapped[pk_uuid] = mapped_column("storage_object_id", default_factory=uuid4)

    # Required
    storage_provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("storage_provider.storage_provider_id"),
        default=None,
    )
    account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("account.account_id", ondelete="SET NULL"),
        default=None,
        index=True,
    )

    object_key: Mapped[str_2000]
    # status: Mapped[Literal["pending", "active", "deleted"]]  # TODO: is status enum needed?
    filename: Mapped[str_2000]
    filesize: Mapped[int] = mapped_column(BigInteger)
    mime_type: Mapped[str_2000]

    # Optional
    created_at: Mapped[current_timestamp] = mapped_column(default=None)

    # Relationships
    provider: Mapped[StorageProvider] = relationship(
        default=None,
        back_populates="storage_objects",
    )
