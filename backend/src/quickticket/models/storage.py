from __future__ import annotations

from uuid import uuid7

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from quickticket.models.base import Base
from quickticket.models.types import (
    StorageObjectID,
    StorageProviderID,
    UserID,
    current_timestamp,
    str_2000,
)

__all__ = (
    "StorageObject",
    "StorageProvider",
)


class StorageProvider(Base, kw_only=True, repr=False):
    __tablename__ = "storage_provider"
    __table_args__ = (UniqueConstraint("endpoint", "region"),)

    id: Mapped[StorageProviderID] = mapped_column(
        "storage_provider_id",
        primary_key=True,
        default_factory=uuid7,
    )

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
        passive_deletes=True,
    )


class StorageObject(Base, kw_only=True, repr=False):
    __tablename__ = "storage_object"

    id: Mapped[StorageObjectID] = mapped_column(
        "storage_object_id",
        primary_key=True,
        default_factory=uuid7,
    )

    # Required
    storage_provider_id: Mapped[StorageProviderID] = mapped_column(
        ForeignKey("storage_provider.storage_provider_id"),
        default=None,
    )
    account_id: Mapped[UserID | None] = mapped_column(
        ForeignKey("account.account_id", ondelete="SET NULL"),
        default=None,
        index=True,
    )

    object_key: Mapped[str_2000]
    # status: Mapped[Literal["pending", "active", "deleted"]]  # TODO: is status enum needed?
    filename: Mapped[str_2000]
    filesize: Mapped[int] = mapped_column(
        BigInteger,
        CheckConstraint("filesize >= 0", "filesize_positive"),
    )
    mime_type: Mapped[str_2000]

    # Optional
    created_at: Mapped[current_timestamp] = mapped_column(default=None)

    # Relationships
    provider: Mapped[StorageProvider] = relationship(
        default=None,
        back_populates="storage_objects",
    )
