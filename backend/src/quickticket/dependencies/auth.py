import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated, Any, NoReturn

from authlib.integrations.base_client import OAuthError
from fastapi import Depends, HTTPException, Query, Request
from fastapi.datastructures import URL
from joserfc import jwt
from joserfc.errors import ExpiredTokenError, JoseError
from joserfc.jwk import KeySet
from joserfc.jwt import JWTClaimsRegistry
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl
from pydantic_core import from_json
from sqlalchemy import select
from sqlalchemy.orm import load_only

from quickticket.dependencies.cache import CacheDep, SettingsDep
from quickticket.dependencies.cookies import (
    COOKIE_OAUTH_POST_REDIRECT,
    OAuthCookieControllerDep,
    OAuthIdTokenCookie,
    OAuthPostRedirectCookie,
    OAuthRefreshTokenCookie,
)
from quickticket.dependencies.db import AsyncSessionDep
from quickticket.dependencies.state import HTTPClientDep
from quickticket.models import User
from quickticket.oauth import OAuth2Client, OpenIDProvider
from quickticket.settings import OpenIDSettings

_CACHE_ERROR_PREFIX = "ERROR"
log = logging.getLogger(__name__)


async def _cache_get_with_error(cache: CacheDep, key: str) -> Any | None:
    ret = await cache.get(key)
    if ret is not None and ret.startswith(_CACHE_ERROR_PREFIX):
        raise HTTPException(500, ret)
    return ret


async def _cache_mark_failed(cache: CacheDep, key: str, message: str) -> NoReturn:
    expiry = timedelta(minutes=1)
    message = f"{_CACHE_ERROR_PREFIX}: {message} (can retry in: {expiry})".rstrip()
    log.warning("Storing error in cache [%s]: %s", key, message)
    await cache.set(key, message, expiry=expiry)
    raise HTTPException(500, message)


async def get_openid_provider(
    http: HTTPClientDep,
    cache: CacheDep,
    settings: SettingsDep,
) -> OpenIDProvider:
    async def fail(message: str = "") -> NoReturn:
        message = f"OpenID discovery is misconfigured ({message})"
        await _cache_mark_failed(cache, cache_key, message)

    async def parse_provider(data: str) -> OpenIDProvider:
        assert settings.openid is not None

        id, secret = settings.openid.client_id, settings.openid.client_secret
        try:
            data = from_json(data)
            return OpenIDProvider(client_id=id, client_secret=secret, discovery=data)
        except ValueError as e:
            log.error("Cannot parse provider", exc_info=e)
            return await fail("malformed response")

    if settings.openid is None:
        raise HTTPException(500, "OpenID is not configured")

    cache_key = "openid-provider-discovery"
    cached = await _cache_get_with_error(cache, cache_key)
    if cached is not None:
        return await parse_provider(cached)

    log.info("Fetching discovery URL from OpenID provider")
    response = await http.get(str(settings.openid.discovery_url))
    if not response.is_success:
        await fail(f"HTTP {response.status_code}")

    provider = await parse_provider(response.text)
    await cache.set(cache_key, response.text, expiry=timedelta(hours=1))
    return provider


async def get_openid_provider_jwks(
    cache: CacheDep,
    http: HTTPClientDep,
    provider: OpenIDProviderDep,
) -> KeySet:
    async def fail(message: str = "") -> NoReturn:
        message = f"OpenID JWKs are misconfigured ({message})"
        await _cache_mark_failed(cache, cache_key, message)

    async def parse_key_set(data: str) -> KeySet:
        try:
            return KeySet.import_key_set(from_json(data))
        except ValueError as e:
            log.error("Cannot parse JWKs", exc_info=e)
            await fail("malformed response")

    cache_key = "openid-provider-jwks"
    cached = await _cache_get_with_error(cache, cache_key)
    if cached is not None:
        return await parse_key_set(cached)

    log.info("Fetching JWKs from OpenID provider")
    response = await http.get(str(provider.discovery.jwks_uri))
    if not response.is_success:
        await fail(f"HTTP {response.status_code}")

    keys = await parse_key_set(response.text)
    await cache.set(cache_key, response.text, expiry=timedelta(hours=1))
    return keys


def get_oauth_client(provider: OpenIDProviderDep) -> OAuth2Client:
    return OAuth2Client(provider)


def get_claims_registry(provider: OpenIDProviderDep) -> JWTClaimsRegistry:
    # https://jose.authlib.org/en/guide/jwt/#validate-claims
    registry = jwt.JWTClaimsRegistry(
        iss={"essential": True, "value": str(provider.discovery.issuer)},
        sub={"essential": True},
        aud={"essential": True, "value": provider.client_id.get_secret_value()},
        exp={"essential": True},
        iat={"essential": True},
        # Identity
        email={"essential": True},
        email_verified={"essential": True, "value": True},
        name={"essential": True},
        given_name={"essential": True},
        family_name={"essential": True},
        preferred_username={"essential": True},
        groups={"essential": True},
    )
    return registry


class IdTokenHeader(BaseModel):
    model_config = ConfigDict(extra="allow")

    alg: str
    typ: str
    kid: str


class IdTokenClaims(BaseModel):
    model_config = ConfigDict(extra="allow")

    # FIXME: likely needs looser validation to support other providers
    exp: int
    iat: int
    auth_time: int
    jti: str
    iss: str
    aud: str
    sub: str
    typ: str
    azp: str
    sid: str
    at_hash: str
    acr: str
    email_verified: bool
    name: str
    groups: list[str] = Field(default_factory=list)
    preferred_username: str
    given_name: str
    family_name: str
    email: EmailStr
    nonce: str | None = None


class IdToken(BaseModel):
    header: IdTokenHeader
    claims: IdTokenClaims
    raw: str


def parse_id_token(
    raw: Annotated[str, OAuthIdTokenCookie],
    keys: OpenIDProviderJWKsDep,
    registry: JWTClaimsRegistryDep,
) -> IdToken:
    # Can raise JoseError exceptions:
    # - BadSignatureError
    # - InvalidPayloadError
    # - InvalidClaimError
    # - MissingClaimError
    token = jwt.decode(raw, keys)
    registry.validate(token.claims)
    return IdToken(header=token.header, claims=token.claims, raw=raw)


async def get_or_refresh_id_token(
    keys: OpenIDProviderJWKsDep,
    registry: JWTClaimsRegistryDep,
    client: OAuth2ClientDep,
    cookies: OAuthCookieControllerDep,
    registration: RegistrationControllerDep,
    # NOTE: below cookies can expire on browser
    id_token_cookie: Annotated[str | None, OAuthIdTokenCookie] = None,
    refresh_token_cookie: Annotated[str | None, OAuthRefreshTokenCookie] = None,
) -> IdToken | None:
    """Attempt to return a valid ID token from the user's cookies.

    If the ID token is invalid and a refresh token is present,
    the server will attempt to fetch a new ID token from the OpenID provider.
    If this fails, both token cookies will be marked for deletion.

    """
    if id_token_cookie is not None:
        # ID token is present, check validity
        try:
            return parse_id_token(id_token_cookie, keys, registry)
        except ExpiredTokenError:
            log.debug("Ignoring expired ID token")
        except JoseError as e:
            log.debug("Ignoring invalid ID token", exc_info=e)

    if refresh_token_cookie is None:
        cookies.delete_tokens()  # flush out invalid ID token if present
        return

    log.debug("Refreshing ID token")
    try:
        tokens = await client.refresh_token(refresh_token_cookie)
    except OAuthError as e:
        if e.error == "invalid_grant":  # provider refused grant_type=refresh_token
            log.debug("OpenID session expired, re-authentication required")
        else:
            log.debug("Failed to refresh ID token", exc_info=e)
        cookies.delete_tokens()
        return

    try:
        id_token = parse_id_token(tokens.id_token, keys, registry)
    except JoseError as e:
        # This suggests conflicting configuration,
        # perhaps incorrect system time or outdated JWKs?
        log.warning("OpenID returned invalid ID token", exc_info=e)
        return

    # CAUTION: a route that returns a Response directly like RedirectResponse
    #          will bypass these cookies! Blame FastAPI
    await registration.register(
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
        refresh_token=tokens.refresh_token,
        refresh_expires_in=tokens.refresh_expires_in,
        id_token=id_token,
    )

    return id_token


def get_valid_id_token(token: OptionalIdTokenDep) -> IdToken:
    if token is None:
        raise HTTPException(401, "Not authenticated")
    return token


def get_allowed_redirect_uri(
    settings: SettingsDep,
    request: Request,
    redirect_uri: Annotated[
        HttpUrl | None,
        Query(
            description=(
                "The URL to redirect after a successful login/logout. "
                "Must match one of the whitelisted ``redirect_uris`` on the server."
            ),
        ),
    ] = None,
) -> URL:
    if redirect_uri is None:
        return URL(str(settings.frontend.default_redirect_uri or request.base_url))
    elif not settings.frontend.match_redirect_uri(redirect_uri):
        raise HTTPException(400, "Invalid redirect_uri= query parameter")
    return URL(str(redirect_uri))


def get_post_redirect_uri(
    settings: SettingsDep,
    request: Request,
    redirect_cookie: Annotated[HttpUrl | None, OAuthPostRedirectCookie] = None,
) -> URL:
    if redirect_cookie is None:
        return URL(str(settings.frontend.default_redirect_uri or request.base_url))
    elif not settings.frontend.match_redirect_uri(redirect_cookie):
        raise HTTPException(400, f"Invalid {COOKIE_OAUTH_POST_REDIRECT} cookie")
    return URL(str(redirect_cookie))


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

    async def register(
        self,
        *,
        access_token: str,  # TODO: fetch userinfo with OAuth2Client?
        expires_in: int,
        refresh_token: str,
        refresh_expires_in: int,
        id_token: IdToken,
    ) -> None:
        claims = id_token.claims
        query = select(User).options(load_only(User.id))
        user = await self.session.scalar(query.where(User.openid_sub == claims.sub))
        if user is None:
            # FIXME: no guarantee two users don't share same email, prompt recommended
            user = await self.session.scalar(query.where(User.email == claims.email))
        if user is None:
            user = User()

        self._update_user_with_claims(user, claims)
        self.session.add(user)

        self.cookies.set_tokens(
            id_token=id_token,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_expires_in,
        )

    def force_redirect(self, url: str | URL, status_code: int) -> NoReturn:
        return self.cookies.force_redirect(url, status_code)

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


async def get_user(id_token: OptionalIdTokenDep, session: AsyncSessionDep) -> User | None:
    if id_token is None:
        return
    query = select(User).where(User.openid_sub == id_token.claims.sub)
    return await session.scalar(query)


async def get_user_or_redirect(
    user: OptionalUserDep,
    cookies: OAuthCookieControllerDep,
    request: Request,
) -> User:
    if user is None:
        url = request.url_for("oauth_login").include_query_params(redirect_uri=request.url)
        cookies.delete_all()
        return cookies.force_redirect(url)
    return user


JWTClaimsRegistryDep = Annotated[JWTClaimsRegistry, Depends(get_claims_registry)]
OAuth2ClientDep = Annotated[OAuth2Client, Depends(get_oauth_client)]
OpenIDProviderDep = Annotated[OpenIDProvider, Depends(get_openid_provider)]
OpenIDProviderJWKsDep = Annotated[KeySet, Depends(get_openid_provider_jwks)]
OptionalIdTokenDep = Annotated[IdToken | None, Depends(get_or_refresh_id_token)]
OptionalUserDep = Annotated[User | None, Depends(get_user)]
PostRedirectUriDep = Annotated[URL, Depends(get_post_redirect_uri)]
RedirectUriDep = Annotated[URL, Depends(get_allowed_redirect_uri)]
RegistrationControllerDep = Annotated[RegistrationController, Depends(RegistrationController)]
RequiredIdTokenDep = Annotated[IdToken, Depends(get_valid_id_token)]
RequiredUserDep = Annotated[User, Depends(get_user_or_redirect)]
