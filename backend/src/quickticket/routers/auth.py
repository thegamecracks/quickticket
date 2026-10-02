import logging
from datetime import timedelta
from typing import Annotated

from authlib.common.security import generate_token
from fastapi import APIRouter, HTTPException, Query, Request
from joserfc.errors import JoseError

from quickticket.dependencies.auth import (
    JWTClaimsRegistryDep,
    OAuth2ClientDep,
    OAuthCookieControllerDep,
    OAuthIdTokenCookie,
    OpenIDProviderJWKsDep,
    OptionalUserDep,
    PostRedirectUriDep,
    RedirectUriDep,
    RegistrationControllerDep,
    RequiredIdTokenDep,
    parse_id_token,
)
from quickticket.dependencies.cache import CacheDep
from quickticket.dependencies.cookies import OAuthNonceCookie, OAuthStateCookie
from quickticket.oauth import FrontchannelLogoutUnsupported

LOGIN_EXPIRY = 1800
LOGOUT_EXPIRY = 1800
CACHE_STATE_TO_CODE_VERIFIER = "oauth-state-{}"

router = APIRouter(tags=["Authentication"])
log = logging.getLogger(__name__)


# https://docs.authlib.org/en/latest/oauth2/client/http/index.html#oidc-session
@router.post(
    "/login",
    responses={303: {"description": "The user is being redirected."}},
    status_code=303,
)
async def oauth_login(
    user: OptionalUserDep,
    redirect_uri: RedirectUriDep,
    request: Request,
    client: OAuth2ClientDep,
    cache: CacheDep,
    cookies: OAuthCookieControllerDep,
):
    """Redirect the user to login at the OpenID provider.

    The ID and refresh token cookies are optional.
    If a valid ID token is provided or the ID token can be refreshed,
    this redirects straight to ``redirect_uri``.

    """
    if user is not None:
        return cookies.force_redirect(redirect_uri, 303)

    # Proof Key for Code Exchange (PKCE)
    code_verifier = generate_token(48)
    # https://openid.net/specs/openid-connect-core-1_0.html#rfc.section.2
    # Nonce to be stored in ID token to prevent replay attacks
    nonce = generate_token()

    url, state = client.create_authorization_url(
        code_verifier=code_verifier,
        nonce=nonce,
        redirect_uri=request.url_for("oauth_post_login"),
    )

    cache_key = CACHE_STATE_TO_CODE_VERIFIER.format(state)
    await cache.set(cache_key, code_verifier, expiry=timedelta(seconds=LOGIN_EXPIRY))

    # https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies
    # https://auth0.com/blog/demystifying-oauth-security-state-vs-nonce-vs-pkce/
    cookies.set_nonce(nonce, max_age=LOGIN_EXPIRY)
    cookies.set_state(state, max_age=LOGIN_EXPIRY)
    cookies.set_post_redirect(redirect_uri, max_age=LOGIN_EXPIRY)
    return cookies.force_redirect(url, 303)


@router.get(
    "/post-login",
    responses={
        303: {"description": "The user successfully logged in."},
        400: {"description": "The token exchange is invalid."},
    },
    status_code=303,
)
async def oauth_post_login(
    # Required
    state_query: Annotated[
        str,
        Query(
            alias="state",
            description="The OAuth2 flow state to validate against the cookie.",
        ),
    ],
    state_cookie: Annotated[str, OAuthStateCookie],
    nonce_cookie: Annotated[str, OAuthNonceCookie],
    # Dependencies
    cache: CacheDep,
    client: OAuth2ClientDep,
    request: Request,
    keys: OpenIDProviderJWKsDep,
    registry: JWTClaimsRegistryDep,
    registration: RegistrationControllerDep,
    # Optional
    redirect_uri: PostRedirectUriDep,
):
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
        redirect_uri=request.url_for("oauth_post_login"),
    )

    # Verify ID token validity + nonce
    try:
        id_token = parse_id_token(tokens.id_token, keys, registry)
    except JoseError as e:
        log.debug("OpenID returned invalid ID token", exc_info=e)
        raise HTTPException(400, "OpenID returned invalid ID token") from e

    if id_token.claims.nonce != nonce_cookie:
        log.debug(
            "ID token nonce does not match nonce cookie (%r != %r)",
            id_token.claims.nonce,
            nonce_cookie,
        )
        raise HTTPException(400, "OpenID returned invalid ID token")

    return await registration.register_and_redirect(
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
        refresh_token=tokens.refresh_token,
        refresh_expires_in=tokens.refresh_expires_in,
        id_token=id_token,
        redirect_uri=redirect_uri,
        status_code=303,
    )


@router.get("/validate")
async def oauth_validate(token: RequiredIdTokenDep):
    """Verify authentication and return the ID token's header and claims."""
    return token


@router.post(
    "/logout",
    responses={307: {"description": "The user is being redirected."}},
    status_code=307,
)
async def oauth_logout(
    cookies: OAuthCookieControllerDep,
    redirect_uri: RedirectUriDep,
    client: OAuth2ClientDep,
    request: Request,
    id_token_hint: Annotated[str | None, OAuthIdTokenCookie] = None,
):
    """Redirect the user to logout at the OpenID provider.

    If no ID token is provided, this redirects straight to ``redirect_uri``.
    If the provider does not support front-channel logout, this clears your
    login cookies immediately and then redirects to ``redirect_uri``.

    """
    if id_token_hint is None:
        return cookies.force_redirect(redirect_uri, 303)

    try:
        url, state = client.create_logout_url(
            id_token_hint=id_token_hint,  # token can be expired/invalid
            post_logout_redirect_uri=str(request.url_for("oauth_post_logout")),
        )
    except FrontchannelLogoutUnsupported:
        # Can't ask user to logout on the OpenID provider
        cookies.delete_all()
        return cookies.force_redirect(redirect_uri, 307)

    cookies.set_state(state, max_age=LOGOUT_EXPIRY)
    cookies.set_post_redirect(redirect_uri, max_age=LOGOUT_EXPIRY)
    return cookies.force_redirect(url, 303)


@router.get(
    "/post-logout",
    responses={
        307: {"description": "The user successfully logged out."},
        400: {"description": "The state is invalid."},
    },
    status_code=307,
)
async def oauth_post_logout(
    # Required
    state_query: Annotated[
        str,
        Query(
            alias="state",
            description="The OAuth2 flow state to validate against the cookie.",
        ),
    ],
    state_cookie: Annotated[str, OAuthStateCookie],
    # Dependencies
    cookies: OAuthCookieControllerDep,
    # Optional
    redirect_uri: PostRedirectUriDep,
):
    if state_query != state_cookie:
        # Cross-site request forgery
        log.debug("?state= query mismatch with state cookie, possible CSRF")
        raise HTTPException(400, "Invalid or expired state")

    cookies.delete_all()
    return cookies.force_redirect(redirect_uri, 307)
