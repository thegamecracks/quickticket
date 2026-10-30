"""Tests for ORM model behavior, such as server/flush-generated defaults."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import User


@pytest.mark.asyncio
async def test_uuid_default() -> None:
    user = User(
        display_name="Display Name",
        first_name="First",
        last_name="Last",
        email="user@example.com",
    )
    assert user.id is not None


@pytest.mark.asyncio
async def test_current_timestamp_server_default(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    async with make_session() as session, session.begin():
        user = User(
            display_name="Display Name",
            first_name="First",
            last_name="Last",
            email="user@example.com",
        )
        assert user.created_at == None  # HACK: bypass ty's dead code lint with equality

        session.add(user)
        await session.flush()
        await session.refresh(user)

        assert user.created_at is not None
