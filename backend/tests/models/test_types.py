from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy.dialects import postgresql

from quickticket.models.types import TZDateTime


def test_bind_param_none() -> None:
    assert TZDateTime().process_bind_param(None, postgresql.dialect()) is None


def test_bind_param_naive_datetime() -> None:
    with pytest.raises(TypeError, match="tzinfo= must be set"):
        TZDateTime().process_bind_param(datetime(2026, 10, 1, 12), postgresql.dialect())  # noqa: DTZ001


def test_bind_param_aware_datetime() -> None:
    value = datetime(2026, 10, 1, 12, tzinfo=timezone(timedelta(hours=-4)))
    assert TZDateTime().process_bind_param(value, postgresql.dialect()) == datetime(2026, 10, 1, 16)  # noqa: DTZ001


def test_result_value_none() -> None:
    assert TZDateTime().process_result_value(None, postgresql.dialect()) is None


def test_result_value_naive_datetime() -> None:
    value = datetime(2026, 10, 1, 16)  # noqa: DTZ001
    result = TZDateTime().process_result_value(value, postgresql.dialect())
    assert result == datetime(2026, 10, 1, 16, tzinfo=UTC)
    assert result is not None
    assert result.tzinfo is UTC


def test_result_value_aware_datetime() -> None:
    value = datetime(2026, 10, 1, 16, tzinfo=UTC)
    assert TZDateTime().process_result_value(value, postgresql.dialect()) is value
