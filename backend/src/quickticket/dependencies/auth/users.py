import logging
from dataclasses import dataclass
from typing import Annotated, NoReturn

from authlib.integrations.base_client import OAuthError
from fastapi import Depends, HTTPException, Request
from fastapi.datastructures import URL
from joserfc.errors import ExpiredTokenError, JoseError
from sqlalchemy import Select, select
from sqlalchemy.orm import load_only
from sqlalchemy.sql.elements import SQLCoreOperations

from quickticket.dependencies.auth.provider import OAuth2ClientDep
from quickticket.dependencies.auth.tokens import (
    AccessToken,
    IdToken,
    TokenValidatorDep,
)
from quickticket.dependencies.cache import SettingsDep
from quickticket.dependencies.cookies import (
    OAuthAccessTokenCookie,
    OAuthCookieControllerDep,
    OAuthRefreshTokenCookie,
)
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.errors import ForcedResponse
from quickticket.models import OpenIDAccount, User
from quickticket.settings import OpenIDSettings

__all__ = (
    "OptionalAccessTokenDep",
    "OptionalUserDep",
    "RegistrationController",
    "RegistrationControllerDep",
    "RequiredAccessTokenDep",
    "RequiredUserDep",
    "get_or_refresh_access_token",
    "get_user",
    "get_user_or_fail",
    "get_valid_access_token",
)

log = logging.getLogger(__name__)


def _matches_token(token: AccessToken | IdToken) -> SQLCoreOperations[bool]:
    claims = token.claims
    condition = User.openid_accounts.issuer == claims.iss and User.openid_accounts.sub == claims.sub
    if (email := getattr(claims, "email", None)) is not None:
        # FIXME: no guarantee two users don't share same email, prompt recommended
        condition = condition or User.email == email
    return condition


@dataclass
class RegistrationController:
    cookies: OAuthCookieControllerDep
    session: AsyncSessionDep
    settings: SettingsDep

    @property
    def admin_group(self) -> str | None:
        return self.openid.admin_group

    @property
    def openid(self) -> OpenIDSettings:
        assert self.settings.openid is not None
        return self.settings.openid

    async def register_and_redirect(
        self,
        *,
        access_token: AccessToken,  # TODO: fetch userinfo with OAuth2Client?
        expires_in: int,
        refresh_token: str,
        refresh_expires_in: int,
        id_token: IdToken,
        redirect_uri: str | URL,
        status_code: int,
    ) -> NoReturn:
        await self._get_user_by_id_token(id_token, register=True)

        self.cookies.set_tokens(
            # id_token=id_token,
            access_token=access_token,
            expires_in=expires_in,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
        )
        # If an exception were to be raised after this method, FastAPI would replace
        # our response object with a new response that is missing our token cookies.
        # As such, we cannot let our route handling continue, and must force a redirect
        # to ensure the user has our cookies stored.
        #
        # To retry a request, pass redirect_uri=request.url and status_code=307.
        return self.cookies.force_redirect(redirect_uri, status_code)

    async def _get_user_by_id_token(
        self,
        id_token: IdToken,
        *,
        query: Select[User] | None = None,
        register: bool = False,
    ) -> User:
        """Get the user associated with an ID token.

        :param id_token: The token linked to the user.
        :param query: The base query to use for retrieving the user.
        :param register:
            If True, allow creating a new user in the current session and
            flushing it, and allow upserting the user with new credentials.
            If the user does not exist, HTTP 401 will be raised with their
            ID token deleted to force re-authentication.
        :returns: The newly created or existing user.

        """
        claims = id_token.claims
        if query is None:
            query = select(User).options(load_only(User.id))

        user = await self.session.scalar(query.where(_matches_token(id_token)))
        if user is None:
            pass
        elif register:
            await self._update_user_with_id_token(user, id_token)
            return user
        else:
            return user

        if not register:
            # User is missing from database and account registration was not expected.
            # Perhaps the backend has changed databases or a sysadmin deleted the user?
            log.warning("Received valid ID token for non-existent user (sub: %s)", claims.sub)

            # HACK: raise HTTPException(401, "Not authenticated") while deleting cookies
            self.cookies.delete_all()
            response = self.cookies.response
            response.status_code = 401
            response.headers["Content-Type"] = "application/json"
            response.body = b'{"detail":"Not authenticated"}'
            raise ForcedResponse(response)

        log.debug("Creating new user from ID token (sub: %s)", claims.sub)
        user = User()
        await self._update_user_with_id_token(user, id_token)
        self.session.add(user)
        await self.session.flush([user])  # Insert without commit
        await self.session.refresh(user)  # Re-fetch attributes, including user ID
        return user

    async def _update_user_with_id_token(self, user: User, id_token: IdToken) -> None:
        # https://openid.net/specs/openid-connect-basic-1_0.html#rfc.section.2.5
        # Consider retrieving claims from userinfo endpoint with access token
        # "picture", "gender", "birthdate", "zoneinfo", "locale", "phone_number", "address"
        # TODO: set optional claims like locale and address
        claims = id_token.claims
        user.display_name = claims.preferred_username or claims.name
        user.first_name = claims.given_name
        user.last_name = claims.family_name
        user.email = claims.email

        groups = claims.groups
        if self.admin_group is not None:
            is_admin = self.admin_group in groups
        else:
            is_admin = None  # noqa: F841
        # TODO: set admin flag or enum on user

        openid_account = await self.session.get(
            OpenIDAccount,
            (claims.iss, claims.sub),
            with_for_update=True,
        )
        if openid_account is None:
            log.debug("Linking new OpenID account")
            user.openid_accounts.append(
                OpenIDAccount(
                    issuer=claims.iss,
                    sub=claims.sub,
                    account_id=user.id,
                    id_token=id_token.raw,
                )
            )
        else:
            openid_account.id_token = id_token.raw


async def get_or_refresh_access_token(
    validator: TokenValidatorDep,
    client: OAuth2ClientDep,
    cookies: OAuthCookieControllerDep,
    registration: RegistrationControllerDep,
    request: Request,
    # NOTE: below cookies can expire on browser
    access_token_cookie: Annotated[str | None, OAuthAccessTokenCookie] = None,
    # id_token_cookie: Annotated[str | None, OAuthIdTokenCookie] = None,
    refresh_token_cookie: Annotated[str | None, OAuthRefreshTokenCookie] = None,
) -> AccessToken | None:
    """Attempt to return a valid access token from the user's cookies.

    If the access token is invalid and a refresh token is present,
    the server will attempt to fetch new tokens from the OpenID provider.
    If this fails, the token cookies will be marked for deletion.

    """
    if access_token_cookie is not None:
        try:
            return validator.parse_access_token(access_token_cookie)
        except ExpiredTokenError:
            log.debug("Ignoring expired access token")
        except JoseError as e:
            log.debug("Ignoring invalid access token", exc_info=e)

    if refresh_token_cookie is None:
        cookies.delete_tokens()  # flush out invalid access token if present
        return

    log.debug("Refreshing access token")
    try:
        tokens = await client.refresh_token(refresh_token_cookie)
    except OAuthError as e:
        if e.error == "invalid_grant":  # provider refused grant_type=refresh_token
            log.debug("OpenID session expired, re-authentication required")
        else:
            log.debug("Failed to refresh access token", exc_info=e)
        cookies.delete_tokens()
        return

    try:
        access_token = validator.parse_access_token(tokens.access_token)
        id_token = validator.parse_id_token(tokens.id_token)
    except JoseError as e:
        # This suggests conflicting configuration,
        # perhaps incorrect system time or outdated JWKs?
        log.warning("OpenID returned invalid tokens", exc_info=e)
        return

    return await registration.register_and_redirect(
        access_token=access_token,
        expires_in=tokens.expires_in,
        refresh_token=tokens.refresh_token,
        refresh_expires_in=tokens.refresh_expires_in,
        id_token=id_token,
        # Retry the current request
        redirect_uri=request.url,
        status_code=307,
    )


def get_valid_access_token(access_token: OptionalAccessTokenDep) -> AccessToken:
    if access_token is None:
        raise HTTPException(401, "Not authenticated")
    return access_token


async def get_user(access_token: OptionalAccessTokenDep, session: AsyncSessionDep) -> User | None:
    if access_token is not None:
        return await session.scalar(select(User).where(_matches_token(access_token)))


async def get_user_or_fail(
    user: OptionalUserDep,
    cookies: OAuthCookieControllerDep,
    request: Request,
) -> User:
    if user is None:
        # This dependency may be used in unsafe routes where the body/method is required.
        # We cannot redirect the user to login without losing their body/method,
        # and we cannot redirect the user to POST /auth/login, so we must return 401.
        raise HTTPException(401, "Not authenticated")
    return user


OptionalAccessTokenDep = Annotated[AccessToken | None, Depends(get_or_refresh_access_token)]
OptionalUserDep = Annotated[User | None, Depends(get_user)]
RegistrationControllerDep = Annotated[RegistrationController, Depends(RegistrationController)]
RequiredAccessTokenDep = Annotated[AccessToken, Depends(get_valid_access_token)]
RequiredUserDep = Annotated[User, Depends(get_user_or_fail)]
