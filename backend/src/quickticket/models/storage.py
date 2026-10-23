from __future__ import annotations

from uuid import UUID

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


class StorageProvider(Base):
    __tablename__ = "storage_provider"
    __table_args__ = (UniqueConstraint("endpoint", "region"),)

    id: Mapped[pk_uuid] = mapped_column("storage_provider_id")
    created_at: Mapped[current_timestamp]

    endpoint: Mapped[str_2000]
    region: Mapped[str_2000]
    bucket: Mapped[str_2000]
    cdn_base_url: Mapped[str_2000]

    storage_objects: Mapped[list[StorageObject]] = relationship(
        back_populates="provider",
    )


class StorageObject(Base):
    __tablename__ = "storage_object"

    id: Mapped[pk_uuid] = mapped_column("storage_object_id")
    storage_provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("storage_provider.storage_provider_id"),
    )
    account_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("account.account_id", ondelete="SET NULL"),
        index=True,
    )
    created_at: Mapped[current_timestamp]

    object_key: Mapped[str_2000]
    # status: Mapped[Literal["pending", "active", "deleted"]]  # TODO: is status enum needed?
    filename: Mapped[str_2000]
    filesize: Mapped[int] = mapped_column(BigInteger)
    mime_type: Mapped[str_2000]

    provider: Mapped[StorageProvider] = relationship(back_populates="storage_objects")
