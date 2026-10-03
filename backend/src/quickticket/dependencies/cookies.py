from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import cached_property
from typing import Annotated, NoReturn
from urllib.parse import quote

from fastapi import Cookie, Depends, FastAPI, Request, Response
from fastapi.datastructures import URL
from starlette.background import BackgroundTask

from quickticket.dependencies.auth.tokens import AccessToken
from quickticket.errors import ForcedResponse

COOKIE_OAUTH_NONCE = "oauth-nonce"
COOKIE_OAUTH_STATE = "oauth-state"
COOKIE_OAUTH_POST_REDIRECT = "oauth-post-redirect"
COOKIE_OAUTH_ACCESS_TOKEN = "oauth-access-token"
COOKIE_OAUTH_REFRESH_TOKEN = "oauth-refresh-token"
# COOKIE_OAUTH_ID_TOKEN = "oauth-id-token"

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
OAuthAccessTokenCookie = Cookie(
    alias=COOKIE_OAUTH_ACCESS_TOKEN,
    description=(
        "The access token received after authentication. "
        "This token is used to make requests to the API."
    ),
)
OAuthRefreshTokenCookie = Cookie(
    alias=COOKIE_OAUTH_REFRESH_TOKEN,
    description=(
        "The refresh token received after authentication. "
        "This token is automatically used by the API to refresh your access token."
    ),
)
# OAuthIdTokenCookie = Cookie(
#     alias=COOKIE_OAUTH_ID_TOKEN,
#     description=(
#         "The ID token received after authentication. This token is used to prove your identity."
#     ),
# )


def cookie_safe_redirect(
    response: Response,
    url: str | URL,
    status_code: int,
    *,
    headers: Mapping[str, str] | None = None,
    background: BackgroundTask | None = None,
) -> NoReturn:
    """Raise a ForcedResponse to redirect the user while preserving headers like cookies.

    This should be used over :class:`pydantic.responses.RedirectResponse`
    because it avoids overwriting headers set by middleware and dependencies.

    """
    # Copied from RedirectResponse body
    response.body = b""
    response.status_code = status_code
    if headers is not None:
        response.headers.update(headers)
    if background is not None:
        response.background = background

    response.headers["location"] = quote(str(url), safe=":/%#?=@[]!$&'()*+,;")
    raise ForcedResponse(response)


@dataclass(kw_only=True, repr=False)
class OAuthCookieController:
    request: Request
    response: Response

    @cached_property
    def auth_path(self) -> str:
        # Feels like a hack...
        return self.app.url_path_for("oauth_login").rpartition("/")[0]

    @property
    def app(self) -> FastAPI:
        return self.request.app

    def set_nonce(self, nonce: str, *, max_age: int) -> None:
        self.response.set_cookie(COOKIE_OAUTH_NONCE, nonce, max_age=max_age, path=self.auth_path)

    def set_state(self, state: str, *, max_age: int) -> None:
        self.response.set_cookie(COOKIE_OAUTH_STATE, state, max_age=max_age, path=self.auth_path)

    def set_post_redirect(self, url: str | URL, *, max_age: int) -> None:
        self.response.set_cookie(
            COOKIE_OAUTH_POST_REDIRECT,
            str(url),
            max_age=max_age,
            path=self.auth_path,
        )

    def set_tokens(
        self,
        *,
        # id_token: IdToken,
        access_token: AccessToken,
        expires_in: int,
        refresh_token: str,
        refresh_expires_in: int,
    ) -> None:
        self.delete_flow()
        self.response.set_cookie(
            COOKIE_OAUTH_ACCESS_TOKEN,
            access_token.raw,
            max_age=expires_in,
        )
        self.response.set_cookie(
            COOKIE_OAUTH_REFRESH_TOKEN,
            refresh_token,
            max_age=refresh_expires_in,
        )
        # self.response.set_cookie(
        #     COOKIE_OAUTH_ID_TOKEN,
        #     id_token.raw,
        #     max_age=id_token.claims.exp - id_token.claims.iat,
        # )

    def delete_flow(self) -> None:
        self.response.delete_cookie(COOKIE_OAUTH_NONCE, path=self.auth_path)
        self.response.delete_cookie(COOKIE_OAUTH_STATE, path=self.auth_path)
        self.response.delete_cookie(COOKIE_OAUTH_POST_REDIRECT, path=self.auth_path)

    def delete_tokens(self) -> None:
        self.response.delete_cookie(COOKIE_OAUTH_ACCESS_TOKEN)
        self.response.delete_cookie(COOKIE_OAUTH_REFRESH_TOKEN)
        # self.response.delete_cookie(COOKIE_OAUTH_ID_TOKEN)

    def delete_all(self) -> None:
        self.delete_flow()
        self.delete_tokens()

    def force_redirect(
        self,
        url: str | URL,
        status_code: int,
        *,
        headers: Mapping[str, str] | None = None,
        background: BackgroundTask | None = None,
    ) -> NoReturn:
        return cookie_safe_redirect(
            self.response,
            url,
            status_code,
            headers=headers,
            background=background,
        )


OAuthCookieControllerDep = Annotated[OAuthCookieController, Depends(OAuthCookieController)]
