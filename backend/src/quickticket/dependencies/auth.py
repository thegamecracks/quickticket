import logging
from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import KeySet
from joserfc.jwt import Token

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
    print("Fetching OpenID discovery url")
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

    response = await http.get(str(provider.discovery.jwks_uri))
    state.openid_provider_jwks = KeySet.import_key_set(response.json())
    return state.openid_provider_jwks


async def get_oauth_client(
    provider: OpenIDProviderDep,
    request: Request,
    state: StateDep,
) -> OAuth2Client:
    client = cast(OAuth2Client | None, getattr(state, "oauth_client", None))
    if client is not None:
        return client

    print("Creating OAuth2 client")
    state.oauth_client = OAuth2Client(
        provider,
        redirect_uri=str(request.url_for("oauth_callback")),
    )
    return state.oauth_client


_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_token(
    keys: OpenIDProviderJWKsDep,
    authorization_header: Annotated[str, Depends(_oauth2_scheme)],
) -> Token:
    try:
        token = jwt.decode(authorization_header, keys)
    except JoseError as e:
        raise HTTPException(
            401,
            "Not authenticated",
            {"WWW-Authenticate": "Bearer"},
        ) from e

    return token


OAuth2ClientDep = Annotated[OAuth2Client, Depends(get_oauth_client)]
OpenIDProviderDep = Annotated[OpenIDProvider, Depends(get_openid_provider)]
OpenIDProviderJWKsDep = Annotated[KeySet, Depends(get_openid_provider_jwks)]
TokenDep = Annotated[Token, Depends(get_token)]
