import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.errors import (
    OrganizationMemberNotFound,
    ORMEntityNotFound,
    UnauthorizedOrganizationMember,
)
from quickticket.models import (
    Organization,
    OrganizationMember,
    OrganizationMemberPermissions,
    Point,
    User,
    Venue,
)
from quickticket.routers.venues import VENUE_LIMIT, VenueCreate, VenueRead, create_venue


@pytest.mark.asyncio
async def test_create_venue(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
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

    request = VenueCreate(
        organization_id=organization.id,
        display_name="Test Venue",
        description="A venue for testing.",
        theme="Sports",
        location_name="Test Stadium",
        location_coords=Point(lat=48.8584, long=2.2945),
    )
    async with make_session() as session, session.begin():
        response = await create_venue(user=user, session=session, venue=request)
        venue = VenueRead.model_validate(response, from_attributes=True)

    assert venue.id is not None
    assert venue.created_at is not None
    assert venue.display_name == "Test Venue"
    assert venue.description == "A venue for testing."
    assert venue.theme == "Sports"
    assert venue.location_name == "Test Stadium"
    assert venue.location_coords == Point(lat=48.8584, long=2.2945)
    assert venue.thumbnail is None
    assert venue.banner is None
    assert venue.events == []
    assert venue.organization.id == organization.id
    assert venue.organization.display_name == "Test Organization"

    async with make_session() as session, session.begin():
        persisted = await session.get(Venue, venue.id)
        assert persisted is not None
        assert persisted.id == venue.id


@pytest.mark.asyncio
async def test_create_venue_nonexistent_organization(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    async with make_session() as session:
        user = User(
            display_name="Display Name",
            first_name="First",
            last_name="Last",
            email="user@example.com",
        )
        session.add(user)
        await session.commit()

    request = VenueCreate(
        organization_id=uuid.uuid4(),
        display_name="Test Venue",
        description="A venue for testing.",
        theme="Sports",
        location_name="Test Stadium",
        location_coords=Point(lat=48.8584, long=2.2945),
    )
    async with make_session() as session, session.begin():
        with pytest.raises(ORMEntityNotFound) as exc_info:
            await create_venue(user=user, session=session, venue=request)

    exc = exc_info.value
    assert exc.entity is Organization
    assert exc.ident == request.organization_id


@pytest.mark.asyncio
async def test_create_venue_non_member(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    async with make_session() as session, session.begin():
        user = User(
            display_name="Display Name",
            first_name="First",
            last_name="Last",
            email="user@example.com",
        )
        organization = Organization(display_name="Test Organization")
        session.add_all([user, organization])

    request = VenueCreate(
        organization_id=organization.id,
        display_name="Test Venue",
        description="A venue for testing.",
        theme="Sports",
        location_name="Test Stadium",
        location_coords=Point(lat=48.8584, long=2.2945),
    )
    async with make_session() as session, session.begin():
        with pytest.raises(OrganizationMemberNotFound) as exc_info:
            await create_venue(user=user, session=session, venue=request)

    exc = exc_info.value
    assert exc.organization.id == organization.id
    assert exc.user.id == user.id


@pytest.mark.asyncio
async def test_create_venue_member_insufficient_permissions(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
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
        session.add_all([user, organization, member])

    request = VenueCreate(
        organization_id=organization.id,
        display_name="Test Venue",
        description="A venue for testing.",
        theme="Sports",
        location_name="Test Stadium",
        location_coords=Point(lat=48.8584, long=2.2945),
    )
    async with make_session() as session, session.begin():
        with pytest.raises(UnauthorizedOrganizationMember) as exc_info:
            await create_venue(user=user, session=session, venue=request)

    exc = exc_info.value
    assert exc.member.organization_id == organization.id
    assert exc.member.account_id == user.id
    assert exc.required is OrganizationMemberPermissions.ADMINISTRATOR
    assert exc.missing is OrganizationMemberPermissions.ADMINISTRATOR


@pytest.mark.asyncio
async def test_create_venue_reached_limit(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
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
        for i in range(VENUE_LIMIT):
            session.add(
                Venue(
                    organization_id=organization.id,
                    display_name=f"Test Venue {i}",
                    description="A venue for testing.",
                    theme="Sports",
                    location_name="Test Stadium",
                    location_coords=Point(lat=48.8584, long=2.2945),
                )
            )

    request = VenueCreate(
        organization_id=organization.id,
        display_name="One Venue Too Many",
        description="A venue for testing.",
        theme="Sports",
        location_name="Test Stadium",
        location_coords=Point(lat=48.8584, long=2.2945),
    )
    async with make_session() as session, session.begin():
        with pytest.raises(HTTPException) as exc_info:
            await create_venue(user=user, session=session, venue=request)

    exc = exc_info.value
    assert exc.status_code == 400
    assert exc.detail == f"Reached maximum venue limit: {VENUE_LIMIT}"
