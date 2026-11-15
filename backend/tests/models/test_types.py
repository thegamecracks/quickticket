from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import BaseModel, ValidationError
from sqlalchemy.dialects import postgresql

from quickticket.models.types import MimeType, MimeTypeSerializer, TZDateTime


class MimeTypeModel(BaseModel):
    mime: MimeType


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


def test_mime_type_valid() -> None:
    mime_type = MimeType("image/svg+xml")
    assert isinstance(mime_type, str)
    assert mime_type == "image/svg+xml"


def test_mime_type_invalid() -> None:
    with pytest.raises(ValueError, match="Invalid mime type"):
        MimeType("text/plain; charset=utf-8")


def test_mime_type_pydantic_valid() -> None:
    model = MimeTypeModel(mime="image/png")
    assert model.mime == "image/png"
    assert type(model.mime) is MimeType
    assert model.model_dump() == {"mime": "image/png"}
    assert type(model.model_dump(mode="json")["mime"]) is str


def test_mime_type_pydantic_invalid() -> None:
    with pytest.raises(ValidationError) as exc_info:
        MimeTypeModel(mime="text/plain; charset=utf-8")
    errors = exc_info.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "value_error"
    assert errors[0]["loc"] == ("mime",)
    assert "Invalid mime type" in errors[0]["msg"]


def test_mime_type_pydantic_prevalidated() -> None:
    value = MimeType("image/svg+xml")
    model = MimeTypeModel(mime=value)
    assert model.mime == value
    assert type(model.mime) is MimeType


def test_mime_type_bind_param_mime_type() -> None:
    value = MimeType("image/png")
    assert MimeTypeSerializer().process_bind_param(value, postgresql.dialect()) == value


def test_mime_type_bind_param_none() -> None:
    assert MimeTypeSerializer().process_bind_param(None, postgresql.dialect()) is None


def test_mime_type_result_value_str() -> None:
    value = "image/png"
    result = MimeTypeSerializer().process_result_value(value, postgresql.dialect())
    assert type(result) is MimeType
    assert result == value


def test_mime_type_result_value_none() -> None:
    assert MimeTypeSerializer().process_result_value(None, postgresql.dialect()) is None
