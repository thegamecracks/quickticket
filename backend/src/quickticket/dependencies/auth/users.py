import logging
from dataclasses import dataclass
from typing import Annotated, NoReturn

from authlib.integrations.base_client import OAuthError
from fastapi import Depends, HTTPException, Request
from fastapi.datastructures import URL
from joserfc.errors import ExpiredTokenError, JoseError
from sqlalchemy import Select, select
from sqlalchemy.orm import load_only

from quickticket.dependencies.auth.provider import OAuth2ClientDep
from quickticket.dependencies.auth.tokens import (
    AccessToken,
    IdToken,
    IdTokenClaims,
    TokenValidatorDep,
    ValidTokens,
)
from quickticket.dependencies.cache import SettingsDep
from quickticket.dependencies.cookies import (
    OAuthAccessTokenCookie,
    OAuthCookieControllerDep,
    OAuthIdTokenCookie,
    OAuthRefreshTokenCookie,
)
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.errors import ForcedResponse
from quickticket.models import User
from quickticket.settings import OpenIDSettings

__all__ = (
    "OptionalTokensDep",
    "OptionalUserDep",
    "RegistrationController",
    "RegistrationControllerDep",
    "RequiredTokensDep",
    "RequiredUserDep",
    "get_or_refresh_tokens",
    "get_user",
    "get_user_or_fail",
    "get_valid_tokens",
)

log = logging.getLogger(__name__)


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
        await self.get_user_by_id_token(id_token, register=True)

        self.cookies.set_tokens(
            id_token=id_token,
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

    async def get_user_by_id_token(
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

        user = await self.session.scalar(query.where(User.openid_sub == claims.sub))
        if user is None:
            # FIXME: allow linking multiple OpenID providers
            # FIXME: no guarantee two users don't share same email, prompt recommended
            user = await self.session.scalar(query.where(User.email == claims.email))

        if user is not None:
            # Found existing user
            if register:
                self._update_user_with_claims(user, claims)
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
        self._update_user_with_claims(user, claims)
        self.session.add(user)
        await self.session.flush([user])  # Insert without commit
        await self.session.refresh(user)  # Re-fetch attributes, including user ID
        return user

    def _update_user_with_claims(self, user: User, claims: IdTokenClaims) -> None:
        # https://openid.net/specs/openid-connect-basic-1_0.html#rfc.section.2.5
        # Consider retrieving claims from userinfo endpoint with access token
        # "picture", "gender", "birthdate", "zoneinfo", "locale", "phone_number", "address"
        user.display_name = claims.preferred_username or claims.name
        user.first_name = claims.given_name
        user.last_name = claims.family_name
        user.email = claims.email
        user.openid_sub = claims.sub

        groups = claims.groups
        if self.admin_group is not None:
            is_admin = self.admin_group in groups
        else:
            is_admin = None  # noqa: F841
        # TODO: set admin flag or enum on user


async def get_or_refresh_tokens(
    validator: TokenValidatorDep,
    client: OAuth2ClientDep,
    cookies: OAuthCookieControllerDep,
    registration: RegistrationControllerDep,
    request: Request,
    # NOTE: below cookies can expire on browser
    access_token_cookie: Annotated[str | None, OAuthAccessTokenCookie] = None,
    id_token_cookie: Annotated[str | None, OAuthIdTokenCookie] = None,
    refresh_token_cookie: Annotated[str | None, OAuthRefreshTokenCookie] = None,
) -> ValidTokens | None:
    """Attempt to return valid tokens from the user's cookies.

    If the tokens are invalid and a refresh token is present,
    the server will attempt to fetch new tokens from the OpenID provider.
    If this fails, the token cookies will be marked for deletion.

    """
    if access_token_cookie is not None and id_token_cookie is not None:
        try:
            parsed = validator.parse_tokens(
                access_token=access_token_cookie,
                id_token=id_token_cookie,
            )
        except ExpiredTokenError:
            log.debug("Ignoring expired tokens")
        except JoseError as e:
            log.debug("Ignoring invalid tokens", exc_info=e)
        else:
            return parsed

    if refresh_token_cookie is None:
        cookies.delete_tokens()  # flush out invalid tokens if present
        return

    log.debug("Refreshing tokens")
    try:
        tokens = await client.refresh_token(refresh_token_cookie)
    except OAuthError as e:
        if e.error == "invalid_grant":  # provider refused grant_type=refresh_token
            log.debug("OpenID session expired, re-authentication required")
        else:
            log.debug("Failed to refresh tokens", exc_info=e)
        cookies.delete_tokens()
        return

    try:
        parsed = validator.parse_tokens(
            access_token=tokens.access_token,
            id_token=tokens.id_token,
        )
    except JoseError as e:
        # This suggests conflicting configuration,
        # perhaps incorrect system time or outdated JWKs?
        log.warning("OpenID returned invalid tokens", exc_info=e)
        return

    return await registration.register_and_redirect(
        access_token=parsed.access_token,
        expires_in=tokens.expires_in,
        refresh_token=tokens.refresh_token,
        refresh_expires_in=tokens.refresh_expires_in,
        id_token=parsed.id_token,
        # Retry the current request
        redirect_uri=request.url,
        status_code=307,
    )


def get_valid_tokens(tokens: OptionalTokensDep) -> ValidTokens:
    if tokens is None:
        raise HTTPException(401, "Not authenticated")
    return tokens


async def get_user(
    tokens: OptionalTokensDep,
    registration: RegistrationControllerDep,
) -> User | None:
    if tokens is not None:
        # Query all User attributes
        return await registration.get_user_by_id_token(tokens.id_token, query=select(User))


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


OptionalTokensDep = Annotated[ValidTokens | None, Depends(get_or_refresh_tokens)]
OptionalUserDep = Annotated[User | None, Depends(get_user)]
RegistrationControllerDep = Annotated[RegistrationController, Depends(RegistrationController)]
RequiredTokensDep = Annotated[ValidTokens, Depends(get_valid_tokens)]
RequiredUserDep = Annotated[User, Depends(get_user_or_fail)]
