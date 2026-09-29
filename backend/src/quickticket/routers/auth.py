import logging
from datetime import timedelta
from typing import Annotated

from authlib.common.security import generate_token
from fastapi import APIRouter, HTTPException, Query, Request, Response
from joserfc.errors import JoseError

from quickticket.dependencies import (
    CacheDep,
    JWTClaimsRegistryDep,
    OAuth2ClientDep,
    OAuthIdTokenCookie,
    OAuthNonceCookie,
    OAuthStateCookie,
    OpenIDProviderJWKsDep,
    OptionalIdTokenDep,
    RequiredIdTokenDep,
)
from quickticket.dependencies.auth import parse_id_token
from quickticket.dependencies.cookies import (
    cookie_safe_redirect,
    delete_oauth_token_cookies,
    set_oauth_nonce_state_cookies,
    set_oauth_token_cookies,
)
from quickticket.oauth import TokenExchangeResponse

LOGIN_EXPIRY = 1800
CACHE_STATE_TO_CODE_VERIFIER = "oauth-state-{}"

router = APIRouter()
log = logging.getLogger(__name__)


# https://docs.authlib.org/en/latest/oauth2/client/http/index.html#oidc-session
@router.get("/login")
async def oauth_login(
    client: OAuth2ClientDep,
    cache: CacheDep,
    id_token: OptionalIdTokenDep,
    request: Request,
    response: Response,
):
    # TODO: parametrize to go to any frontend page, perhaps using /path cookie?
    if id_token is not None:
        return cookie_safe_redirect(response, request.url_for("oauth_validate"))

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
    set_oauth_nonce_state_cookies(
        response,
        nonce=nonce,
        state=state,
        max_age=LOGIN_EXPIRY,
    )
    return cookie_safe_redirect(response, url, 302)


@router.get("/callback")
async def oauth_callback(
    # User-provided
    state_query: Annotated[str | None, Query(alias="state")],
    state_cookie: Annotated[str, OAuthStateCookie],
    nonce_cookie: Annotated[str, OAuthNonceCookie],
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
        id_token = parse_id_token(tokens.id_token, keys, registry)
    except JoseError as e:
        log.debug("OpenID returned invalid ID token", exc_info=e)
        raise HTTPException(400, "OpenID returned invalid ID token") from e

    id_token_nonce = id_token.claims.get("nonce")
    if id_token_nonce != nonce_cookie:
        log.debug(
            "ID token nonce does not match nonce cookie (%r != %r)",
            id_token_nonce,
            nonce_cookie,
        )
        raise HTTPException(400, "OpenID returned invalid ID token")

    # TODO: upsert user model with latest identity

    # FIXME: which cookies need to be saved on browser?
    id_token_expires_in = id_token.claims["exp"] - id_token.claims["iat"]
    set_oauth_token_cookies(response, tokens, id_token_expires_in=id_token_expires_in)

    # TODO: parametrize to go to any frontend page, perhaps using /path cookie?
    return tokens


@router.get("/validate")
async def oauth_validate(token: RequiredIdTokenDep):
    return token


@router.get("/logout")
async def oauth_logout(
    client: OAuth2ClientDep,
    request: Request,
    response: Response,
    id_token_hint: Annotated[str | None, OAuthIdTokenCookie] = None,
):
    if id_token_hint is None:
        return await oauth_post_logout(request, response)

    url = client.create_logout_url(
        id_token_hint=id_token_hint,  # token can be expired/invalid
        post_logout_redirect_uri=str(request.url_for("oauth_post_logout")),
    )
    return cookie_safe_redirect(response, url, 302)


@router.get("/post-logout")
async def oauth_post_logout(request: Request, response: Response):
    # TODO: parametrize to go to any frontend page, perhaps using /path cookie?
    delete_oauth_token_cookies(response)
    return cookie_safe_redirect(response, request.url_for("root"), 302)
