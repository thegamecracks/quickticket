import pytest
from fastapi.datastructures import State
from obstore.store import MemoryStore

from quickticket.dependencies.store import get_object_store
from quickticket.settings import S3Settings, Settings


@pytest.mark.asyncio
async def test_memory_store_from_url() -> None:
    settings = Settings(
        _env_file=None,
        s3=S3Settings(
            url="memory:///",
            region="us-east-1",
            access_key="test-access-key",
            secret_key="test-secret-key",  # noqa: S106
        ),
    )
    state = State()

    store = await get_object_store(settings=settings, state=state)
    assert isinstance(store, MemoryStore)
