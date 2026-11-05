"""Tests for ORM model behavior, such as server/flush-generated defaults."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import MoneySerializer, User


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
    async with make_session.begin() as session:
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


@pytest.mark.asyncio
async def test_persisting_timezone_aware_datetime(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    async with make_session.begin() as session:
        user = User(
            display_name="Display Name",
            first_name="First",
            last_name="Last",
            email="user@example.com",
            created_at=datetime(2026, 10, 1, tzinfo=UTC),
        )
        session.add(user)

    async with make_session.begin() as session:
        saved = await session.get(User, user.id)

    assert saved is not None
    assert saved.created_at.tzinfo is not None
    assert saved.created_at == user.created_at


def test_money_serializer_postgresql_dialect() -> None:
    serializer = MoneySerializer()
    impl = serializer.load_dialect_impl(postgresql.dialect())
    assert isinstance(impl, JSONB)
