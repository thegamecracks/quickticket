import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from joserfc.errors import JoseError
from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload

from quickticket.dependencies.auth import OpenIDProviderDep
from quickticket.dependencies.auth.tokens import AccessToken, TokenValidatorDep, UserInfo
from quickticket.dependencies.cache import SettingsDep
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.dependencies.state import HTTPClientDep
from quickticket.models import OpenIDIdentity, User
from quickticket.settings import OpenIDSettings

__all__ = (
    "OptionalAccessTokenDep",
    "OptionalOpenIDIdentityDep",
    "OptionalUserDep",
    "RegistrationController",
    "RegistrationControllerDep",
    "RequiredAccessTokenDep",
    "RequiredUserDep",
    "get_access_token",
    "get_user",
    "get_user_or_fail",
    "get_valid_access_token",
)

FRESH_USERINFO_PERIOD = timedelta(minutes=5)

log = logging.getLogger(__name__)


@dataclass
class RegistrationController:
    http: HTTPClientDep
    provider: OpenIDProviderDep
    session: AsyncSessionDep
    settings: SettingsDep

    @property
    def admin_group(self) -> str | None:
        return self.openid.admin_group

    @property
    def openid(self) -> OpenIDSettings:
        assert self.settings.openid is not None
        return self.settings.openid

    async def select_user_by_token(self, token: AccessToken) -> tuple[User, OpenIDIdentity]:
        """Get the user associated with an access token along with the
        OpenID identity they used to login.

        :param token: The access token linked to the user.
        :param query: The base query to use for retrieving the user.
        :returns: The newly created or existing user.

        """
        user: User | None = None
        claims = token.claims

        identity = await self.session.scalar(
            select(OpenIDIdentity)
            .join(User, OpenIDIdentity.user)
            .where(OpenIDIdentity.issuer == claims.iss, OpenIDIdentity.sub == claims.sub)
            .options(load_only(OpenIDIdentity.user_id), selectinload(OpenIDIdentity.user)),
        )
        if identity is not None:
            user = identity.user
            await self._maybe_refresh_userinfo(user, token)
            return user, identity

        if (email := getattr(claims, "email", None)) is not None and getattr(
            claims,
            "email_verified",
            False,
        ) is True:
            # Link email claim from access token if present
            # TODO: no guarantee two users don't share same email, prompt recommended
            user = await self.session.scalar(select(User).where(User.email == email))

        if user is not None:
            log.debug("Linking new OpenID identity with access token")
            identity = OpenIDIdentity(issuer=claims.iss, sub=claims.sub, user_id=user.id)
            self.session.add(identity)

            await self._maybe_refresh_userinfo(user, token)
            await self.session.flush()  # May flush entities outside of our dependency
            await self.session.refresh(identity)

            return user, identity

        log.debug("Registering new user from access token (sub: %s)", claims.sub)
        user = User(display_name="", first_name="", last_name="", email="")
        identity = OpenIDIdentity(issuer=claims.iss, sub=claims.sub)
        user.openid_identities.append(identity)
        self.session.add(user)

        await self._maybe_refresh_userinfo(user, token)
        await self.session.flush()  # May flush entities outside of our dependency
        await self.session.refresh(user)  # Re-fetch attributes, including user ID

        return user, identity

    async def _maybe_refresh_userinfo(self, user: User, token: AccessToken) -> None:
        updated_at = user.userinfo_updated_at  # fools type-checker, can be None if newly created
        if updated_at is not None and datetime.now(UTC) - updated_at < FRESH_USERINFO_PERIOD:
            return

        log.debug("Refreshing userinfo from provider (sub: %s)", token.claims.sub)
        claims = await self._fetch_userinfo(token)
        self._update_user_with_userinfo(user, claims)

    async def _fetch_userinfo(self, token: AccessToken) -> UserInfo:
        headers = {"Authorization": f"Bearer {token.raw}"}
        userinfo_endpoint = str(self.provider.discovery.userinfo_endpoint)
        response = await self.http.get(userinfo_endpoint, headers=headers)
        response.raise_for_status()
        claims = response.json()
        return UserInfo.model_validate(claims)

    def _update_user_with_userinfo(self, user: User, claims: UserInfo) -> None:
        # https://openid.net/specs/openid-connect-basic-1_0.html#rfc.section.2.5
        # "picture", "gender", "birthdate", "zoneinfo", "locale", "phone_number", "address"
        # TODO: set optional claims like locale and address
        user.display_name = claims.preferred_username or claims.name
        user.first_name = claims.given_name
        user.last_name = claims.family_name
        user.email = claims.email

        groups = claims.groups
        if self.admin_group is not None:  # noqa: SIM108
            is_admin = self.admin_group in groups
        else:
            is_admin = None  # noqa: F841
        # TODO: set admin flag or enum on user


async def get_access_token(
    validator: TokenValidatorDep,
    access_token: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
) -> AccessToken | None:
    try:
        return validator.parse_access_token(access_token.credentials)
    except JoseError as e:
        log.debug("Ignoring invalid bearer token (%s)", e)
        raise HTTPException(401, "Not authenticated", {"WWW-Authenticate": "Bearer"}) from e


async def get_valid_access_token(access_token: OptionalAccessTokenDep) -> AccessToken:
    if access_token is None:
        raise HTTPException(401, "Not authenticated")
    return access_token


async def get_user(
    access_token: OptionalAccessTokenDep,
    registration: RegistrationControllerDep,
) -> User | None:
    if access_token is not None:
        # This may fetch the user twice if their access token had to be refreshed.
        user, _ = await registration.select_user_by_token(access_token)
        return user
    return None


async def get_user_or_fail(user: OptionalUserDep) -> User:
    if user is None:
        # This dependency may be used in unsafe routes where the body/method is required.
        # We cannot redirect the user to login without losing their body/method,
        # and we cannot redirect the user to POST /auth/login, so we must return 401.
        raise HTTPException(401, "Not authenticated")
    return user


async def get_openid_identity(
    access_token: OptionalAccessTokenDep,
    registration: RegistrationControllerDep,
) -> OpenIDIdentity | None:
    if access_token is not None:
        _, identity = await registration.select_user_by_token(access_token)
        return identity
    return None


OptionalAccessTokenDep = Annotated[AccessToken | None, Depends(get_access_token)]
OptionalOpenIDIdentityDep = Annotated[OpenIDIdentity | None, Depends(get_openid_identity)]
OptionalUserDep = Annotated[User | None, Depends(get_user)]
RegistrationControllerDep = Annotated[RegistrationController, Depends(RegistrationController)]
RequiredAccessTokenDep = Annotated[AccessToken, Depends(get_valid_access_token)]
RequiredUserDep = Annotated[User, Depends(get_user_or_fail)]
