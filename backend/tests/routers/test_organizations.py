import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from quickticket.models import OrganizationMember, OrganizationMemberPermissions, User
from quickticket.routers.organizations import (
    OrganizationCreate,
    OrganizationRead,
    create_organization,
)


@pytest.mark.asyncio
async def test_create_organization(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    async with make_session() as session, session.begin():
        user = User(
            display_name="Display Name",
            first_name="First",
            last_name="Last",
            email="user@example.com",
        )

        request = OrganizationCreate(display_name="Test Organization")
        response = await create_organization(user=user, session=session, organization=request)
        organization = OrganizationRead.model_validate(response, from_attributes=True)

    assert organization.id is not None
    assert organization.created_at is not None
    assert organization.display_name == "Test Organization"
    assert organization.venues == []
    assert organization.members[0].account_id == user.id

    async with make_session() as session, session.begin():
        member = await session.get(OrganizationMember, (organization.id, user.id))
        assert member is not None
        assert member.permissions == OrganizationMemberPermissions.ADMINISTRATOR


@pytest.mark.asyncio
async def test_create_organization_one_owner_only(
    make_session: async_sessionmaker[AsyncSession],
) -> None:
    async with make_session() as session, session.begin():
        user = User(
            display_name="Display Name",
            first_name="First",
            last_name="Last",
            email="user@example.com",
        )

        request = OrganizationCreate(display_name="First Organization")
        response = await create_organization(user=user, session=session, organization=request)

    async with make_session() as session, session.begin():
        with pytest.raises(HTTPException) as exc_info:
            await create_organization(
                user=user,
                session=session,
                organization=OrganizationCreate(display_name="Second Organization"),
            )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Already owns an organization"
    assert response.display_name == "First Organization"


def test_create_organization_rejects_blank_display_name() -> None:
    with pytest.raises(ValidationError):
        OrganizationCreate(display_name="")


def test_create_organization_rejects_overlong_display_name() -> None:
    with pytest.raises(ValidationError):
        OrganizationCreate(display_name="x" * 129)
