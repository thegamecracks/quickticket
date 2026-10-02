"""This is a minimal frontend to be used for testing purposes.

It can be disabled with BACKEND__FRONTEND__BUILTIN=0.

"""

import logging
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from quickticket.dependencies.auth import OpenIDProviderDep, OptionalAccessTokenDep, OptionalUserDep
from quickticket.dependencies.state import SettingsDep
from quickticket.routers.profile import profile_me

_BASE_DIR = Path(__file__).parent

router = APIRouter(include_in_schema=False)
static = StaticFiles(directory=_BASE_DIR / "static")
templates = Jinja2Templates(directory=_BASE_DIR / "templates")
log = logging.getLogger(__name__)


@router.get("/")
async def frontend_root(
    request: Request,
    settings: SettingsDep,
    access_token: OptionalAccessTokenDep,
    provider: OpenIDProviderDep,
    user: OptionalUserDep,
) -> HTMLResponse:
    redirect_uri = str(settings.frontend.default_redirect_uri or request.base_url)
    context = {
        "now": datetime.now(UTC),
        # Authentication
        "discovery": provider.discovery,
        "discovery_url": settings.openid and settings.openid.discovery_url,
        "access_token": access_token and access_token.claims,
        "access_token_iat": access_token and datetime.fromtimestamp(access_token.claims.iat, UTC),
        "access_token_exp": access_token and datetime.fromtimestamp(access_token.claims.exp, UTC),
        # Frontend
        "cors_origins": settings.frontend.origins,
        "default_redirect_uri": redirect_uri,
        # Database
        "profile": user and await profile_me(user),
    }
    return templates.TemplateResponse(request, "index.html.j2", context)


@router.get("/events")
async def frontend_events(request: Request, user: OptionalUserDep) -> HTMLResponse:
    context = {"profile": user and await profile_me(user)}
    return templates.TemplateResponse(request, "events.html.j2", context)
