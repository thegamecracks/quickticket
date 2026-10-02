import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request
from fastapi.datastructures import URL
from pydantic import HttpUrl

from quickticket.dependencies.cache import SettingsDep
from quickticket.dependencies.cookies import COOKIE_OAUTH_POST_REDIRECT, OAuthPostRedirectCookie

__all__ = (
    "PostRedirectUriDep",
    "RedirectUriDep",
    "get_allowed_redirect_uri",
    "get_post_redirect_uri",
)

log = logging.getLogger(__name__)


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


PostRedirectUriDep = Annotated[URL, Depends(get_post_redirect_uri)]
RedirectUriDep = Annotated[URL, Depends(get_allowed_redirect_uri)]
