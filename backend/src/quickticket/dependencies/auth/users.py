import logging
from dataclasses import dataclass
from typing import Annotated, NoReturn

from authlib.integrations.base_client import OAuthError
from fastapi import Depends, HTTPException, Request
from fastapi.datastructures import URL
from joserfc.errors import ExpiredTokenError, JoseError
from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload

from quickticket.dependencies.auth.provider import OAuth2ClientDep
from quickticket.dependencies.auth.tokens import AccessToken, IdToken, TokenValidatorDep
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
    "OptionalOpenIDAccountDep",
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
        await self.select_user_by_token(id_token)

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

    async def select_user_by_token(
        self,
        token: AccessToken | IdToken,
    ) -> tuple[User, OpenIDAccount]:
        """Get the user associated with an ID or access token along with the
        OpenID account they used to login.

        If an ID token is passed, the user will be registered for a new account
        if necessary and their personal details will be updated.
        If an access token is passed and the user does not exist, an HTTP 401
        will be raised with their token cookies deleted to force re-authentication.

        :param token: The ID or access token linked to the user.
        :param query: The base query to use for retrieving the user.
        :returns: The newly created or existing user.

        """
        claims = token.claims

        # get openid account
        # if account is present
        #     update user
        #     return user and account

        # get user by email
        # if user is present
        #     create openid account
        #     return user and account

        # if not registering
        #     fail login

        # create user and account
        # return user and account

        openid_account = await self.session.scalar(
            select(OpenIDAccount)
            .join(User, OpenIDAccount.user)
            .where(OpenIDAccount.issuer == claims.iss, OpenIDAccount.sub == claims.sub)
            .options(load_only(OpenIDAccount.account_id), selectinload(OpenIDAccount.user))
        )
        if openid_account is not None:
            user = openid_account.user
            if isinstance(token, IdToken):
                self._update_openid_account(openid_account, token)
                self._update_user_with_id_token(user, token)
            return user, openid_account

        if (email := getattr(token, "email", None)) is not None:
            # Link email claim from either access or ID token if present
            # FIXME: no guarantee two users don't share same email, prompt recommended
            user = await self.session.scalar(select(User).where(User.email == email))

        if user is not None:
            if isinstance(token, IdToken):
                log.debug("Linking new OpenID account with ID token")
                id_token_raw = token.raw
            else:
                # Access token is insufficient for RP-initiated logout.
                # We'll need to get the ID token later by doing a refresh.
                log.debug("Linking new OpenID account with access token")
                id_token_raw = None

            openid_account = OpenIDAccount(
                issuer=claims.iss,
                sub=claims.sub,
                account_id=user.id,
                id_token=id_token_raw,
            )
            user.openid_accounts.append(openid_account)
            return user, openid_account

        if isinstance(token, AccessToken):
            # User is missing from database and account registration was not expected.
            # Perhaps the backend has changed databases or a sysadmin deleted the user?
            log.warning("Received access token for non-existent user (sub: %s)", claims.sub)

            # HACK: raise HTTPException(401, "Not authenticated") while deleting cookies
            self.cookies.delete_all()
            response = self.cookies.response
            response.status_code = 401
            response.headers["Content-Type"] = "application/json"
            response.body = b'{"detail":"Not authenticated"}'
            raise ForcedResponse(response)

        log.debug("Registering new user from ID token (sub: %s)", claims.sub)
        user = User()
        openid_account = OpenIDAccount(issuer=claims.iss, sub=claims.sub)
        user.openid_accounts.append(openid_account)
        self._update_openid_account(openid_account, token)
        self._update_user_with_id_token(user, token)

        self.session.add(user)
        await self.session.flush([user, openid_account])  # Insert without commit
        await self.session.refresh(user)  # Re-fetch attributes, including user ID

        return user, openid_account

    def _update_user_with_id_token(self, user: User, id_token: IdToken) -> None:
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

    def _update_openid_account(self, openid_account: OpenIDAccount, id_token: IdToken) -> None:
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


async def get_user(
    access_token: OptionalAccessTokenDep,
    registration: RegistrationControllerDep,
) -> User | None:
    if access_token is not None:
        user, _ = await registration.select_user_by_token(access_token)
        return user


async def get_user_or_fail(user: OptionalUserDep) -> User:
    if user is None:
        # This dependency may be used in unsafe routes where the body/method is required.
        # We cannot redirect the user to login without losing their body/method,
        # and we cannot redirect the user to POST /auth/login, so we must return 401.
        raise HTTPException(401, "Not authenticated")
    return user


async def get_openid_account(
    access_token: OptionalAccessTokenDep,
    registration: RegistrationControllerDep,
) -> OpenIDAccount | None:
    if access_token is not None:
        _, openid_account = await registration.select_user_by_token(access_token)
        return openid_account


OptionalAccessTokenDep = Annotated[AccessToken | None, Depends(get_or_refresh_access_token)]
OptionalOpenIDAccountDep = Annotated[OpenIDAccount | None, Depends(get_openid_account)]
OptionalUserDep = Annotated[User | None, Depends(get_user)]
RegistrationControllerDep = Annotated[RegistrationController, Depends(RegistrationController)]
RequiredAccessTokenDep = Annotated[AccessToken, Depends(get_valid_access_token)]
RequiredUserDep = Annotated[User, Depends(get_user_or_fail)]
