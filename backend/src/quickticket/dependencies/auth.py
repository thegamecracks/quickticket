import logging
from typing import Annotated, cast

from fastapi import Cookie, Depends, HTTPException, Request
from joserfc import jwt
from joserfc.errors import ExpiredTokenError, JoseError
from joserfc.jwk import KeySet
from joserfc.jwt import JWTClaimsRegistry, Token

from quickticket import cookies
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
        redirect_uri=str(request.url_for("oauth_callback")),
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


def get_id_token(
    raw: IdTokenRawDep,
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


def get_or_refresh_id_token(
    raw_id_token: IdTokenRawDep,
    keys: OpenIDProviderJWKsDep,
    registry: JWTClaimsRegistryDep,
) -> Token:
    try:
        return get_id_token(raw_id_token, keys, registry)
    except ExpiredTokenError as e:
        # TODO: automatically refresh on backend? do ID tokens expire?
        log.debug("", exc_info=True)
        raise HTTPException(401, "Not authenticated") from e
    except JoseError as e:
        # Cannot set "WWW-Authenticate": "Bearer" for cookie-based authentication
        log.debug("", exc_info=True)
        raise HTTPException(401, "Not authenticated") from e


AccessTokenRawDep = Annotated[str, Cookie(alias=cookies.COOKIE_OAUTH_ACCESS_TOKEN)]
IdTokenDep = Annotated[Token, Depends(get_or_refresh_id_token)]
IdTokenRawDep = Annotated[str, Cookie(alias=cookies.COOKIE_OAUTH_ID_TOKEN)]
JWTClaimsRegistryDep = Annotated[JWTClaimsRegistry, Depends(get_claims_registry)]
OAuth2ClientDep = Annotated[OAuth2Client, Depends(get_oauth_client)]
OpenIDProviderDep = Annotated[OpenIDProvider, Depends(get_openid_provider)]
OpenIDProviderJWKsDep = Annotated[KeySet, Depends(get_openid_provider_jwks)]
RefreshTokenRawDep = Annotated[str, Cookie(alias=cookies.COOKIE_OAUTH_REFRESH_TOKEN)]
