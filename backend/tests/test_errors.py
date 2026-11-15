from uuid import UUID

from quickticket.errors import ORMEntityNotFound
from quickticket.models import Venue


def test_orm_entity_not_found_formats_single_identifier() -> None:
    ident = UUID("00000000-0000-0000-0000-000000000001")

    exc = ORMEntityNotFound(Venue, ident)

    assert exc.entity is Venue
    assert exc.ident == ident
    assert str(exc) == f"Venue not found: {ident}"


def test_orm_entity_not_found_formats_composite_identifier() -> None:
    ident = (
        UUID("00000000-0000-0000-0000-000000000001"),
        UUID("00000000-0000-0000-0000-000000000002"),
    )

    exc = ORMEntityNotFound(Venue, ident)

    assert exc.entity is Venue
    assert exc.ident == ident
    assert str(exc) == f"Venue not found: ({ident[0]}, {ident[1]})"
