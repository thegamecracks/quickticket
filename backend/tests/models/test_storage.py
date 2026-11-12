import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import StorageObject, StorageProvider
from quickticket.models.types import MimeType


@pytest.mark.asyncio
async def test_mime_type_round_trip(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    async with make_session.begin() as session:
        provider = StorageProvider(
            endpoint="https://s3.example.com",
            region="us-east-1",
            bucket="quickticket",
            cdn_base_url="https://cdn.example.com",
        )
        session.add(provider)
        await session.flush()

        obj = StorageObject(
            storage_provider_id=provider.id,
            object_key="banners/example.png",
            filename="example.png",
            filesize=1024,
            mime_type=MimeType("image/png"),
        )
        session.add(obj)

    async with make_session.begin() as session:
        saved = await session.get(StorageObject, obj.id)

    assert saved is not None
    assert type(saved.mime_type) is MimeType
    assert saved.mime_type == MimeType("image/png")
