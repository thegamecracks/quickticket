from collections.abc import Mapping
from urllib.parse import quote

from fastapi import Cookie, Response
from fastapi.datastructures import URL
from starlette.background import BackgroundTask

from quickticket.oauth import TokenExchangeResponse

__all__ = (
    # "COOKIE_OAUTH_ACCESS_TOKEN",
    "COOKIE_OAUTH_ID_TOKEN",
    "COOKIE_OAUTH_NONCE",
    "COOKIE_OAUTH_POST_REDIRECT",
    "COOKIE_OAUTH_REFRESH_TOKEN",
    "COOKIE_OAUTH_STATE",
    # "OAuthAccessTokenCookie",
    "OAuthIdTokenCookie",
    "OAuthNonceCookie",
    "OAuthPostRedirectCookie",
    "OAuthRefreshTokenCookie",
    "OAuthStateCookie",
    "cookie_safe_redirect",
    "delete_all_oauth_cookies",
    "delete_oauth_flow_cookies",
    "delete_oauth_token_cookies",
    "set_oauth_nonce_cookie",
    "set_oauth_post_redirect_cookie",
    "set_oauth_state_cookie",
    "set_oauth_token_cookies",
)

COOKIE_OAUTH_NONCE = "oauth-nonce"
COOKIE_OAUTH_STATE = "oauth-state"
COOKIE_OAUTH_POST_REDIRECT = "oauth-post-redirect"
# COOKIE_OAUTH_ACCESS_TOKEN = "oauth-access-token"
COOKIE_OAUTH_REFRESH_TOKEN = "oauth-refresh-token"
COOKIE_OAUTH_ID_TOKEN = "oauth-id-token"

OAuthNonceCookie = Cookie(
    alias=COOKIE_OAUTH_NONCE,
    description="The OAuth2 flow nonce for login.",
)
OAuthStateCookie = Cookie(
    alias=COOKIE_OAUTH_STATE,
    description="The OAuth2 flow state for login/logout.",
)
OAuthPostRedirectCookie = Cookie(
    alias=COOKIE_OAUTH_POST_REDIRECT,
    description="The URL to redirect after a successful login/logout.",
)
# OAuthAccessTokenCookie = Cookie(
#     alias=COOKIE_OAUTH_ACCESS_TOKEN,
#     description=(
#         "The access token received after authentication. "
#         "This token is used to make requests to the OpenID provider's API."
#         # To my understanding, access tokens can be opaque strings so we can't
#         # validate its authenticity from our client unless we sent a request
#         # to the provider each time.
#         # The ID token on the other hand is signed by a publicly available key
#         # in the JWKs URL (JSON Web Keys), so we can cache the keys and verify
#         # ID tokens client-side.
#     ),
# )
OAuthRefreshTokenCookie = Cookie(
    alias=COOKIE_OAUTH_REFRESH_TOKEN,
    description=(
        "The refresh token received after authentication. "
        "This token is automatically used by the API to refresh your ID token."
    ),
)
OAuthIdTokenCookie = Cookie(
    alias=COOKIE_OAUTH_ID_TOKEN,
    description=(
        "The ID token received after authentication. "
        "This token is used to prove your identity."
    ),
)


# TODO: restrict flow cookies by /auth path
def set_oauth_nonce_cookie(
    response: Response,
    nonce: str,
    *,
    max_age: int,
) -> None:
    response.set_cookie(
        COOKIE_OAUTH_NONCE,
        nonce,
        httponly=True,
        max_age=max_age,
        secure=True,
    )


def set_oauth_state_cookie(
    response: Response,
    state: str,
    *,
    max_age: int,
) -> None:
    response.set_cookie(
        COOKIE_OAUTH_STATE,
        state,
        httponly=True,
        max_age=max_age,
        secure=True,
    )


def set_oauth_post_redirect_cookie(
    response: Response,
    url: str | URL,
    *,
    max_age: int,
) -> None:
    response.set_cookie(
        COOKIE_OAUTH_POST_REDIRECT,
        str(url),
        httponly=True,
        max_age=max_age,
        secure=True,
    )


def delete_oauth_flow_cookies(response: Response) -> None:
    response.delete_cookie(COOKIE_OAUTH_NONCE, httponly=True, secure=True)
    response.delete_cookie(COOKIE_OAUTH_STATE, httponly=True, secure=True)
    response.delete_cookie(COOKIE_OAUTH_POST_REDIRECT, httponly=True, secure=True)


def set_oauth_token_cookies(
    response: Response,
    tokens: TokenExchangeResponse,
    *,
    id_token_expires_in: int,
) -> None:
    delete_oauth_flow_cookies(response)
    # response.set_cookie(
    #     COOKIE_OAUTH_ACCESS_TOKEN,
    #     tokens.access_token,
    #     httponly=True,
    #     max_age=int(tokens.expires_in),
    #     secure=True,
    # )
    response.set_cookie(
        COOKIE_OAUTH_REFRESH_TOKEN,
        tokens.refresh_token,
        httponly=True,
        max_age=int(tokens.refresh_expires_in),
        secure=True,
    )
    response.set_cookie(
        COOKIE_OAUTH_ID_TOKEN,
        tokens.id_token,
        httponly=True,
        max_age=id_token_expires_in,
        secure=True,
    )


def delete_all_oauth_cookies(response: Response) -> None:
    delete_oauth_flow_cookies(response)
    delete_oauth_token_cookies(response)


def delete_oauth_token_cookies(response: Response) -> None:
    # response.delete_cookie(COOKIE_OAUTH_ACCESS_TOKEN, httponly=True, secure=True)
    response.delete_cookie(COOKIE_OAUTH_REFRESH_TOKEN, httponly=True, secure=True)
    response.delete_cookie(COOKIE_OAUTH_ID_TOKEN, httponly=True, secure=True)


def cookie_safe_redirect(
    response: Response,
    url: str | URL,
    status_code: int = 307,
    *,
    headers: Mapping[str, str] | None = None,
    background: BackgroundTask | None = None,
) -> Response:
    """Set a response to redirect the user without.

    This should be used over :class:`pydantic.responses.RedirectResponse`
    because it avoids overwriting cookies set by middleware or dependencies.

    """
    # Copied from RedirectResponse body
    response.body = b""
    response.status_code = status_code
    if headers is not None:
        response.headers.update(headers)
    if background is not None:
        response.background = background

    response.headers["location"] = quote(str(url), safe=":/%#?=@[]!$&'()*+,;")
    return response
