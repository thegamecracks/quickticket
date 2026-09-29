import logging
from typing import Annotated, cast

from authlib.integrations.base_client import OAuthError
from fastapi import Depends, HTTPException, Request, Response
from joserfc import jwt
from joserfc.errors import ExpiredTokenError, JoseError
from joserfc.jwk import KeySet
from joserfc.jwt import JWTClaimsRegistry, Token

from quickticket.dependencies.cookies import (
    OAuthIdTokenCookie,
    OAuthRefreshTokenCookie,
    set_oauth_token_cookies,
)
from quickticket.dependencies.state import HTTPClientDep, SettingsDep, StateDep
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
    http: HTTPClientDep,
    provider: OpenIDProviderDep,
    state: StateDep,
) -> KeySet:
    keys = cast(KeySet | None, getattr(state, "openid_provider_jwks", None))
    if keys is not None:
        return keys

    log.info("Fetching JWKs from OpenID provider")
    response = await http.get(str(provider.discovery.jwks_uri))
    state.openid_provider_jwks = KeySet.import_key_set(response.json())
    return state.openid_provider_jwks


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
    response: Response,
    # NOTE: below cookies can expire on browser
    id_token_cookie: Annotated[str | None, OAuthIdTokenCookie] = None,
    refresh_token_cookie: Annotated[str | None, OAuthRefreshTokenCookie] = None,
) -> Token | None:
    if id_token_cookie is not None:
        # ID token is present, check validity
        try:
            return parse_id_token(id_token_cookie, keys, registry)
        except ExpiredTokenError:
            log.debug("Ignoring expired ID token")
        except JoseError as e:
            log.debug("Ignoring invalid ID token", exc_info=e)

    if refresh_token_cookie is None:
        return

    log.debug("Refreshing ID token")
    try:
        tokens = await client.refresh_token(refresh_token_cookie)
    except OAuthError as e:
        if e.error == "invalid_grant":  # provider refused grant_type=refresh_token
            log.debug("OpenID session expired, re-authentication required")
        else:
            log.debug("Failed to refresh ID token", exc_info=e)
        # TODO: redirect to provider for login, then redirect back to request.url?
        return

    try:
        id_token = parse_id_token(tokens.id_token, keys, registry)
    except JoseError as e:
        log.debug("OpenID returned invalid ID token", exc_info=e)
        return

    # CAUTION: a route that returns a Response directly like RedirectResponse
    #          will bypass these cookies! Blame FastAPI
    id_token_expires_in = id_token.claims["exp"] - id_token.claims["iat"]
    set_oauth_token_cookies(response, tokens, id_token_expires_in=id_token_expires_in)
    # TODO: update user model with latest userinfo

    return id_token


def get_valid_id_token(token: OptionalIdTokenDep) -> Token:
    if token is None:
        raise HTTPException(401, "Not authenticated")
    return token


JWTClaimsRegistryDep = Annotated[JWTClaimsRegistry, Depends(get_claims_registry)]
OAuth2ClientDep = Annotated[OAuth2Client, Depends(get_oauth_client)]
OpenIDProviderDep = Annotated[OpenIDProvider, Depends(get_openid_provider)]
OpenIDProviderJWKsDep = Annotated[KeySet, Depends(get_openid_provider_jwks)]
OptionalIdTokenDep = Annotated[Token | None, Depends(get_or_refresh_id_token)]
RequiredIdTokenDep = Annotated[Token, Depends(get_valid_id_token)]
