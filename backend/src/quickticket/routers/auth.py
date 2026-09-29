import logging
from datetime import timedelta
from typing import Annotated

from authlib.common.security import generate_token
from fastapi import APIRouter, Cookie, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from joserfc.errors import JoseError

from quickticket import cookies
from quickticket.dependencies import (
    CacheDep,
    IdTokenDep,
    IdTokenRawDep,
    JWTClaimsRegistryDep,
    OAuth2ClientDep,
    OpenIDProviderJWKsDep,
)
from quickticket.dependencies.auth import get_id_token
from quickticket.oauth import TokenExchangeResponse

LOGIN_EXPIRY = 1800
CACHE_STATE_TO_CODE_VERIFIER = "oauth-state-{}"

router = APIRouter()
log = logging.getLogger(__name__)


# https://docs.authlib.org/en/latest/oauth2/client/http/index.html#oidc-session
@router.get("/login")
async def oauth_login(client: OAuth2ClientDep, cache: CacheDep) -> RedirectResponse:
    # Proof Key for Code Exchange (PKCE)
    code_verifier = generate_token(48)
    # https://openid.net/specs/openid-connect-core-1_0.html#rfc.section.2
    # Nonce to be stored in ID token to prevent replay attacks
    nonce = generate_token()

    url, state = client.create_authorization_url(
        code_verifier=code_verifier,
        nonce=nonce,
    )

    cache_key = CACHE_STATE_TO_CODE_VERIFIER.format(state)
    await cache.set(cache_key, code_verifier, expiry=timedelta(seconds=LOGIN_EXPIRY))

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies
    # https://auth0.com/blog/demystifying-oauth-security-state-vs-nonce-vs-pkce/
    response = RedirectResponse(url, 302)
    response.set_cookie(
        cookies.COOKIE_OAUTH_NONCE,
        nonce,
        httponly=True,
        max_age=LOGIN_EXPIRY,
        secure=True,
    )
    response.set_cookie(
        cookies.COOKIE_OAUTH_STATE,
        state,
        httponly=True,
        max_age=LOGIN_EXPIRY,
        secure=True,
    )

    return response
    # return {"nonce": nonce, "state": state, "url": url}


@router.get("/callback")
async def oauth_callback(
    # User-provided
    state_query: Annotated[str | None, Query(alias="state")],
    state_cookie: Annotated[str, Cookie(alias=cookies.COOKIE_OAUTH_STATE)],
    nonce_cookie: Annotated[str, Cookie(alias=cookies.COOKIE_OAUTH_NONCE)],
    # Dependencies
    keys: OpenIDProviderJWKsDep,
    registry: JWTClaimsRegistryDep,
    cache: CacheDep,
    request: Request,
    response: Response,
    client: OAuth2ClientDep,
) -> TokenExchangeResponse:
    if state_query != state_cookie:
        # Cross-site request forgery
        log.debug("?state= query mismatch with state cookie, possible CSRF")
        raise HTTPException(400, "Invalid or expired state")

    cache_key = CACHE_STATE_TO_CODE_VERIFIER.format(state_query)
    code_verifier = await cache.pop(cache_key)
    if code_verifier is None:
        log.debug("Code verifier missing from cache")
        raise HTTPException(400, "Invalid or expired state")

    tokens = await client.fetch_token(
        authorization_response=str(request.url),
        code_verifier=code_verifier,
    )

    # Verify ID token validity + nonce
    try:
        id_token = get_id_token(tokens.id_token, keys, registry)
    except JoseError as e:
        log.debug("Cannot validate ID token: %s", e, exc_info=e)
        raise HTTPException(400, "OpenID returned invalid token") from e

    log.debug("id_token.header = %r", id_token.header)
    log.debug("id_token.claims = %r", id_token.claims)

    id_token_nonce = id_token.claims.get("nonce")
    if id_token_nonce != nonce_cookie:
        log.debug(
            "ID token nonce does not match nonce cookie (%r != %r)",
            id_token_nonce,
            nonce_cookie,
        )
        raise HTTPException(400, "OpenID returned invalid token")

    # TODO: upsert user model with latest identity

    # FIXME: which cookies need to be saved on browser?
    response.delete_cookie(cookies.COOKIE_OAUTH_NONCE, httponly=True, secure=True)
    response.delete_cookie(cookies.COOKIE_OAUTH_STATE, httponly=True, secure=True)
    response.set_cookie(
        cookies.COOKIE_OAUTH_ACCESS_TOKEN,
        tokens.access_token,
        httponly=True,
        max_age=int(tokens.expires_in),
        secure=True,
    )
    response.set_cookie(
        cookies.COOKIE_OAUTH_REFRESH_TOKEN,
        tokens.refresh_token,
        httponly=True,
        max_age=int(tokens.refresh_expires_in),
        secure=True,
    )
    response.set_cookie(
        cookies.COOKIE_OAUTH_ID_TOKEN,
        tokens.id_token,
        httponly=True,
        max_age=id_token.claims["exp"] - id_token.claims["iat"],
        secure=True,
    )

    # TODO: parametrize to go to any frontend page
    return tokens


@router.get("/validate")
async def oauth_validate(token: IdTokenDep):
    return token


@router.get("/logout")
async def oauth_logout(
    token: IdTokenRawDep,
    client: OAuth2ClientDep,
    request: Request,
) -> RedirectResponse:
    url = client.create_logout_url(
        id_token=token,
        post_logout_redirect_uri=str(request.url_for("oauth_post_logout")),
    )
    return RedirectResponse(url, 302)


@router.get("/post-logout")
async def oauth_post_logout(request: Request) -> RedirectResponse:
    # TODO: parametrize to go to any frontend page
    response = RedirectResponse(request.url_for("root"), 302)
    response.delete_cookie(
        cookies.COOKIE_OAUTH_ACCESS_TOKEN,
        httponly=True,
        secure=True,
    )
    response.delete_cookie(
        cookies.COOKIE_OAUTH_REFRESH_TOKEN,
        httponly=True,
        secure=True,
    )
    response.delete_cookie(
        cookies.COOKIE_OAUTH_ID_TOKEN,
        httponly=True,
        secure=True,
    )
    return response
