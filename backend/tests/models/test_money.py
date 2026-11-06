from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB

from quickticket.models import MoneySerializer


def test_money_serializer_postgresql_dialect() -> None:
    serializer = MoneySerializer()
    impl = serializer.load_dialect_impl(postgresql.dialect())
    assert isinstance(impl, JSONB)
