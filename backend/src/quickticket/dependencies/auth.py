import logging
from datetime import timedelta
from typing import Annotated, NoReturn, cast

from authlib.integrations.base_client import OAuthError
from fastapi import Depends, HTTPException, Query, Request
from fastapi.datastructures import URL
from joserfc import jwt
from joserfc.errors import ExpiredTokenError, JoseError
from joserfc.jwk import KeySet
from joserfc.jwt import JWTClaimsRegistry, Token
from pydantic import HttpUrl
from pydantic_core import from_json

from quickticket.dependencies.cache import (
    CacheDep,
    SettingsDep,
    StateDep,
)
from quickticket.dependencies.cookies import (
    COOKIE_OAUTH_POST_REDIRECT,
    OAuthCookieControllerDep,
    OAuthIdTokenCookie,
    OAuthPostRedirectCookie,
    OAuthRefreshTokenCookie,
)
from quickticket.dependencies.state import HTTPClientDep
from quickticket.oauth import OAuth2Client, OpenIDProvider

log = logging.getLogger(__name__)


async def get_openid_provider(
    http: HTTPClientDep,
    state: StateDep,
    settings: SettingsDep,
) -> OpenIDProvider:
    provider = cast(
        OpenIDProvider | None,
        getattr(state, "openid_provider", None),
    )
    if provider is not None:
        return provider

    if settings.openid is None:
        raise HTTPException(404, "OpenID is not configured for this backend")

    # FIXME: exceptions here can result in spamming the discovery URL
    log.info("Fetching discovery URL from OpenID provider")
    response = await http.get(str(settings.openid.discovery_url))
    state.openid_provider = OpenIDProvider(
        client_id=settings.openid.client_id,
        client_secret=settings.openid.client_secret,
        discovery=response.json(),
    )

    return state.openid_provider


async def get_openid_provider_jwks(
    cache: CacheDep,
    http: HTTPClientDep,
    provider: OpenIDProviderDep,
) -> KeySet:
    async def fail(short: str = "", full: str = "") -> NoReturn:
        expiry = timedelta(minutes=10)
        message = (
            full
            or f"ERROR: OpenID JWKs are misconfigured, please wait {expiry} minutes to try again. ({short})"
        )
        await cache.set(cache_key, message, expiry=expiry)
        raise HTTPException(500, message)

    cache_key = "openid-provider-jwks"
    json = await cache.get(cache_key)
    cached = json is not None

    if not cached:
        log.info("Fetching JWKs from OpenID provider")

        response = await http.get(str(provider.discovery.jwks_uri))
        if not response.is_success:
            await fail(f"HTTP {response.status_code}")

        json = response.text

    elif json.startswith("ERROR"):
        await fail(full=json)

    try:
        keys = KeySet.import_key_set(from_json(json))
    except ValueError:
        await fail("JWKs response is malformed")

    if not cached:
        # Who knows how long to cache this
        await cache.set(cache_key, json, expiry=timedelta(hours=1))

    return keys


def get_oauth_client(
    provider: OpenIDProviderDep,
    request: Request,
    state: StateDep,
) -> OAuth2Client:
    client = cast(OAuth2Client | None, getattr(state, "oauth_client", None))
    if client is not None:
        return client

    log.info("Initializing OAuth2 client")
    state.oauth_client = OAuth2Client(
        provider,
        redirect_uri=str(request.url_for("oauth_post_login")),
    )
    return state.oauth_client


def get_claims_registry(provider: OpenIDProviderDep) -> JWTClaimsRegistry:
    # https://jose.authlib.org/en/guide/jwt/#validate-claims
    registry = jwt.JWTClaimsRegistry(
        iss={"essential": True, "value": str(provider.discovery.issuer)},
        sub={"essential": True},
        aud={"essential": True, "value": provider.client_id.get_secret_value()},
        exp={"essential": True},
        iat={"essential": True},
    )
    return registry


def parse_id_token(
    raw: Annotated[str, OAuthIdTokenCookie],
    keys: OpenIDProviderJWKsDep,
    registry: JWTClaimsRegistryDep,
) -> Token:
    # Can raise JoseError exceptions:
    # - BadSignatureError
    # - InvalidPayloadError
    # - InvalidClaimError
    # - MissingClaimError
    token = jwt.decode(raw, keys)
    registry.validate(token.claims)
    return token


async def get_or_refresh_id_token(
    keys: OpenIDProviderJWKsDep,
    registry: JWTClaimsRegistryDep,
    client: OAuth2ClientDep,
    cookies: OAuthCookieControllerDep,
    # NOTE: below cookies can expire on browser
    id_token_cookie: Annotated[str | None, OAuthIdTokenCookie] = None,
    refresh_token_cookie: Annotated[str | None, OAuthRefreshTokenCookie] = None,
) -> Token | None:
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
    id_token_expires_in = id_token.claims["exp"] - id_token.claims["iat"]
    cookies.set_tokens(tokens, id_token_expires_in=id_token_expires_in)
    # TODO: update user model with latest userinfo

    return id_token


def get_valid_id_token(token: OptionalIdTokenDep) -> Token:
    if token is None:
        raise HTTPException(401, "Not authenticated")
    return token


def get_allowed_redirect_uri(
    settings: SettingsDep,
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
        return URL(str(settings.frontend.default_redirect_uri))
    elif not settings.frontend.match_redirect_uri(redirect_uri):
        raise HTTPException(400, "Invalid redirect_uri= query parameter")
    return URL(str(redirect_uri))


def get_post_redirect_uri(
    settings: SettingsDep,
    redirect_cookie: Annotated[HttpUrl | None, OAuthPostRedirectCookie] = None,
) -> URL:
    if redirect_cookie is None:
        return URL(str(settings.frontend.default_redirect_uri))
    elif not settings.frontend.match_redirect_uri(redirect_cookie):
        raise HTTPException(400, f"Invalid {COOKIE_OAUTH_POST_REDIRECT} cookie")
    return URL(str(redirect_cookie))


JWTClaimsRegistryDep = Annotated[JWTClaimsRegistry, Depends(get_claims_registry)]
OAuth2ClientDep = Annotated[OAuth2Client, Depends(get_oauth_client)]
OpenIDProviderDep = Annotated[OpenIDProvider, Depends(get_openid_provider)]
OpenIDProviderJWKsDep = Annotated[KeySet, Depends(get_openid_provider_jwks)]
OptionalIdTokenDep = Annotated[Token | None, Depends(get_or_refresh_id_token)]
PostRedirectUriDep = Annotated[URL, Depends(get_post_redirect_uri)]
RedirectUriDep = Annotated[URL, Depends(get_allowed_redirect_uri)]
RequiredIdTokenDep = Annotated[Token, Depends(get_valid_id_token)]

__all__ = (
    "JWTClaimsRegistryDep",
    "OAuth2ClientDep",
    "OpenIDProviderDep",
    "OpenIDProviderJWKsDep",
    "OptionalIdTokenDep",
    "PostRedirectUriDep",
    "RedirectUriDep",
    "RequiredIdTokenDep",
)
