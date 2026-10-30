"""Tests for ORM model behavior, such as server/flush-generated defaults."""

import pytest

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
