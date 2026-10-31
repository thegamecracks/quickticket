from datetime import datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.errors import ORMEntityNotFound, UnauthorizedOrganizationMember
from quickticket.models.accounts import User
from quickticket.models.events import Event, Venue
from quickticket.models.money import Money
from quickticket.models.organizations import (
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
)
from quickticket.models.types import Point
from quickticket.routers.events import EventCreate, EventRead, EventsRead, create_event, get_events
from tests.conftest import DatasetLoader


@pytest.mark.asyncio
async def test_create_event(make_session: async_sessionmaker[AsyncSession]) -> None:
    async with make_session() as session, session.begin():
        user = User(
            display_name="Display Name",
            first_name="First",
            last_name="Last",
            email="user@example.com",
        )
        organization = Organization(display_name="Test Organization")
        member = OrganizationMember(
            organization_id=organization.id,
            account_id=user.id,
            permissions=OrganizationMemberPermissions.ADMINISTRATOR,
        )
        venue = Venue(
            organization_id=organization.id,
            display_name="Test Venue",
            description="A venue for testing.",
            theme="Sports",
            location_name="Test Stadium",
            location_coords=Point(lat=48.8584, long=2.2945),
        )
        session.add_all([user, organization, member, venue])

    request = EventCreate(
        venue_id=venue.id,
        display_name="Test Hockey Tournament",
        description="A mock hockey game, for testing.",
        theme="Sports",
        # should display jan 1st, 2027, 6-10pm
        starts_at=datetime(2027, 1, 1, 18, 0),
        ends_at=datetime(2027, 1, 1, 22, 0),
        max_attendees=500,
        ticket_price=Money(amount=50, currency="CAD"),
    )

    async with make_session() as session, session.begin():
        response = await create_event(user=user, session=session, event=request)
        event = EventRead.model_validate(response, from_attributes=True)

    assert event.id is not None
    assert event.created_at is not None
    assert event.display_name == "Test Hockey Tournament"
    assert event.description == "A mock hockey game, for testing."
    assert event.starts_at == datetime(2027, 1, 1, 18, 0)
    assert event.ends_at == datetime(2027, 1, 1, 22, 0)
    assert event.ticket_price == Money(amount=50, currency="CAD")
    assert event.max_attendees == 500
    assert event.venue.id == venue.id

    # assert event.venue.display_name == "Test Venue"
    # assert event.venue.description == "A venue for testing."
    # assert event.venue.theme == "Sports"
    # assert event.venue.location_name == "Test Stadium"
    # assert event.venue.location_coords == Point(lat=48.8584, long=2.2945)

    # assert event.venue.organization.display_name == "Test Organization"

    async with make_session() as session, session.begin():
        persisted = await session.get(Event, event.id)
        assert persisted is not None
        assert persisted.id == event.id


@pytest.mark.asyncio
async def test_create_event_no_permissions(make_session: async_sessionmaker[AsyncSession]) -> None:
    async with make_session() as session, session.begin():
        user = User(
            display_name="Display Name",
            first_name="First",
            last_name="Last",
            email="user@example.com",
        )
        organization = Organization(display_name="Test Organization")
        member = OrganizationMember(
            organization_id=organization.id,
            account_id=user.id,
            permissions=OrganizationMemberPermissions(0),
        )
        venue = Venue(
            organization_id=organization.id,
            display_name="Test Venue",
            description="A venue for testing.",
            theme="Sports",
            location_name="Test Stadium",
            location_coords=Point(lat=48.8584, long=2.2945),
        )
        session.add_all([user, organization, member, venue])

    request = EventCreate(
        venue_id=venue.id,
        display_name="Test Hockey Tournament",
        description="A mock hockey game, for testing.",
        theme="Sports",
        # should display jan 1st, 2027, 6-10pm
        starts_at=datetime(2027, 1, 1, 18, 0),
        ends_at=datetime(2027, 1, 1, 22, 0),
        max_attendees=500,
        ticket_price=Money(amount=50, currency="CAD"),
    )

    async with make_session() as session, session.begin():
        with pytest.raises(UnauthorizedOrganizationMember) as exc_info:
            await create_event(user=user, session=session, event=request)

    exc = exc_info.value
    assert exc.member.organization_id == organization.id
    assert exc.member.account_id == user.id
    assert exc.required is OrganizationMemberPermissions.ADMINISTRATOR
    assert exc.missing is OrganizationMemberPermissions.ADMINISTRATOR


@pytest.mark.asyncio
async def test_create_event_no_venue(make_session: async_sessionmaker[AsyncSession]) -> None:
    async with make_session() as session, session.begin():
        user = User(
            display_name="Display Name",
            first_name="First",
            last_name="Last",
            email="user@example.com",
        )
        organization = Organization(display_name="Test Organization")
        member = OrganizationMember(
            organization_id=organization.id,
            account_id=user.id,
            permissions=OrganizationMemberPermissions.ADMINISTRATOR,
        )
        session.add_all([user, organization, member])

    request = EventCreate(
        venue_id=uuid4(),  # random, no venue
        display_name="Test Hockey Tournament",
        description="A mock hockey game, for testing.",
        theme="Sports",
        # should display jan 1st, 2027, 6-10pm
        starts_at=datetime(2027, 1, 1, 18, 0),
        ends_at=datetime(2027, 1, 1, 22, 0),
        max_attendees=500,
        ticket_price=Money(amount=50, currency="CAD"),
    )

    async with make_session() as session, session.begin():
        with pytest.raises(ORMEntityNotFound) as exc_info:
            await create_event(user=user, session=session, event=request)

    exc = exc_info.value
    assert exc.entity is Venue
    assert exc.ident == request.venue_id


@pytest.mark.asyncio
async def test_get_events(
    dataset_loader: DatasetLoader,
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    await dataset_loader.load()

    async with make_session() as session, session.begin():
        response = await get_events(user=None, session=session)
        response = EventsRead.model_validate(response, from_attributes=True)

    # TODO: validate full payload? would be noisy with the descriptions though...
    event_ids = (
        UUID("ec2eb2b0-22d7-40c0-96f0-6f799227eba4"),
        UUID("97067d2e-7a1c-4451-ac3a-a8e974e1c6e3"),
        UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
        UUID("df8af935-6315-4a0f-9723-e4b031458a4d"),
        UUID("697102d3-6f53-4c93-b65b-f87a36a9b301"),
        UUID("5a1231e3-8e9a-4e87-9835-6db515975d7c"),
        UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
        UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
        UUID("21afa1a9-a4ed-4d2f-8908-93b743027fec"),
        UUID("0e161235-9c40-45e6-b4cd-022fd852f6e6"),
    )

    assert len(response.events) == len(event_ids)
    for i, event_id in enumerate(event_ids):
        assert response.events[i].id == event_id
